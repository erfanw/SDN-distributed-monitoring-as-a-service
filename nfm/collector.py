import json

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (CONFIG_DISPATCHER, DEAD_DISPATCHER,
                                    MAIN_DISPATCHER, set_ev_cls)
from ryu.lib import hub
from ryu.ofproto import ofproto_v1_3

from dm_client_api import delete, select_all, select_last, write
from event import (EventCalculateAverageBandwidth, EventCalculateDropRate,
                   EventCalculateMedianBW, EventDataUpdate, EventProcessStats,
                   EventTopoUpdate, EventWriteDataToDB)
from link_cap_api import get_link_capacity


class StatsCollector(app_manager.RyuApp):

    _EVENTS = [
        EventProcessStats,
        EventCalculateAverageBandwidth, 
        EventWriteDataToDB, 
        EventCalculateDropRate,
        EventDataUpdate
    ]

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *_args, **_kwargs):
        super().__init__(*_args, **_kwargs)
        # datapath id -> datapath object 
        self.datapaths = {} 
        '''
        a dict identify link
        {
            'src_dpid' : null, 
            'src_port' : null,
            'dst_dpid' : null, 
            'dst_port' : null
        }
        topology is a list of links 
        [
            link0, 
            link1, 
            .....
        ]
        '''
        self.topology = []
        '''
        link_stats is a dict depicting link stats 
        link_stats_history is a dict storing link stats, a tuple (src, src_port) identify link_stats
        link_stats : {
            'dst_dpid' : 
            'dst_port' : 
            'rx_at_dst' : 
            'tx_at_src' : 
            'timestamp' : 
            ’itv': 
            'bw' : 
            'drop_rate' : 
        }
        {
            ('src_dpid', 'src_port') : link_stats, 
            .... 
        }
        '''
        self.link_stats_history = {}
        '''
        a dic to store the packets absorbed and emitted by the switch, for calculating packet loss on a specific switch 
        {
            dpid : {
                old_tx_sum : 
                old_rx_sum : 
            }
        }
        '''
        self.switch_stats_history = {}
        self.monitor_thread = None
         # sem for thread safty 
        self.sem = hub.Semaphore()
        # determine wheather switches and links are exhuasted 
        self.switch_counter = 0

        self.avg_bw_history = 0
        self.med_bw_history = 0

        self.switch_history = {}

        self.round = 0


    # topology update event handler, update local links info 
    @set_ev_cls(EventTopoUpdate)
    def topology_update_handler(self, ev): 
        if not self.monitor_thread: 
            # trigger monitor thread 
            self.monitor_thread = hub.spawn(self.monitor)
        if self.sem.acquire(): 
            self.topology = ev.topology
            self.counter = len(self.topology)
            self.sem.release()

    def monitor(self): 
        def _request_port_stats(dpid):
                datapath = self.datapaths[dpid]
                parser = datapath.ofproto_parser
                ofproto = datapath.ofproto
                # port status request 
                req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
                datapath.send_msg(req)
        while True:
            for dp in self.datapaths:
                _request_port_stats(dp)
            self.send_event_to_observers(EventDataUpdate())
            hub.sleep(2)
            self.round += 1

    # handle incoming port stats, parse the port data and trigger statistics processing 
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_handler(self, ev): 
        body = ev.msg.body
        datapath = ev.msg.datapath
        dpid = '%016x' % datapath.id
        self.send_event_to_observers(EventProcessStats(dpid, body))

    # subscribe to EventProcessStats, calculate loss on switch 
    # @set_ev_cls(EventProcessStats)
    def calculate_packet_loss_on_switch(self, ev): 
        dpid = ev.dpid 
        switch_ports_stats = ev.port_stats
        print(switch_ports_stats)
        new_tx_sum = 0
        new_rx_sum = 0

        for port in switch_ports_stats: 
            # print("%s at %s, rx is %s, tx is %s", port.port_no, dpid, new_rx_sum, new_tx_sum)
            new_tx_sum += port.tx_packets
            new_rx_sum += port.rx_packets

        # fetch the old rx_sum and tx_sum 
        if not dpid in self.switch_history:
            old_tx_sum = 0
            old_rx_sum = 0
            self.switch_history[dpid] = {}
        else: 
            old_tx_sum = self.switch_history[dpid]['old_tx_sum']
            old_rx_sum = self.switch_history[dpid]['old_rx_sum']

        # avoid dividing zero 
        if new_rx_sum == old_rx_sum: 
            loss = 0 
        else: 
            loss = (new_rx_sum - new_tx_sum - old_rx_sum + old_tx_sum) / (new_rx_sum - old_rx_sum)

        loss_str = str(round(loss*100, 2)) + "%"

        print("loss at %s is %s" %(dpid, loss_str))
        self.switch_history[dpid] = {
            'old_tx_sum' : new_tx_sum, 
            'old_rx_sum' : new_rx_sum
        }

        data = [
                {
                    "fields": {
                        "loss": round(loss, 2)
                    }, 
                    "tags": {
                        "dpid": dpid
                    }, 
                    "measurement": "sw_drop_rate"
                }
        ] 
        # write(data)


    # subscribe to EventProcessStats, calculate bandwidth 
    @set_ev_cls(EventProcessStats)
    def calculate_bandwidth_on_link(self, ev): 
        dpid = ev.dpid 
        switch_ports_stats = ev.port_stats
        
        # acqure sem for thread safty 
        if self.sem.acquire(): 
            links = [l for l in self.topology if l['dst_dpid'] == dpid]
            self.sem.release()
        for l in links: 
            self.counter -= 1
            src_dpid = l['src_dpid']
            src_port = l['src_port']
            dst_dpid = l['dst_dpid']
            dst_port = l['dst_port']

            port = [p for p in switch_ports_stats if '%08x' % p.port_no == dst_port][0]

            new_timestamp = port.duration_sec + port.duration_nsec * (10 **(-9))
            new_rx = port.rx_bytes
            new_tx = port.tx_bytes
            # if history has not been initiated 
            if not (src_dpid, src_port) in self.link_stats_history.keys():
                old_rx = 0
                old_timestamp = 0
                self.link_stats_history[(src_dpid, src_port)] = {}
            # we have history 
            else : 
                # set default val just in case 
                old_rx = self.link_stats_history[(src_dpid, src_port)].get('rx_at_dst', 0)
                old_timestamp = self.link_stats_history[(src_dpid, src_port)].get('timestamp', 0)

            # apparently calculate bw 
            rx_bytes = new_rx - old_rx
            duration = new_timestamp - old_timestamp
            
            link_capacity_dict = get_link_capacity()
            link_cap = link_capacity_dict[src_dpid][dst_dpid]
            bw = (rx_bytes / duration) /link_cap/1000000 * 8


            # push data to DB onif data has varied 
            data = [
                    {
                        "fields": {
                            "bw": round(bw, 2), 
                            "round" : self.round
                            },
                        "tags": {
                            "src_dpid": src_dpid,
                            "dst_dpid": dst_dpid, 
                            "src_port" : src_port, 
                            "dst_port" : dst_port
                            },
                        "measurement": "links_bw"
                    }
                ] 
            write(data)

            
            # update history, store current data in history for next time 
            self.link_stats_history[(src_dpid, src_port)]['dst_dpid'] = dst_dpid
            self.link_stats_history[(src_dpid, src_port)]['dst_port'] = dst_port
            self.link_stats_history[(src_dpid, src_port)]['rx_at_dst'] = new_rx
            self.link_stats_history[(src_dpid, src_port)]['timestamp'] = new_timestamp
            self.link_stats_history[(src_dpid, src_port)]['bw'] = bw
            self.logger.info('link at %s ---> %s, link utilization is %.2f', src_dpid, dst_dpid, bw)

            '''
            update tx_at_src at reverse link, to calculate drop rate 
            '''
            # but if reverse link history has not been inited 
            if not (dst_dpid, dst_port) in self.link_stats_history.keys(): 
                self.link_stats_history[(dst_dpid, dst_port)] = {}
            self.link_stats_history[(dst_dpid, dst_port)]['tx_at_src'] = new_tx

            # all links have been visited, it's time to calculate drop rate on link and average bandwidth 
            if self.counter == 0: 
                self.send_event_to_observers(EventCalculateAverageBandwidth())
                self.send_event_to_observers(EventCalculateDropRate())
                self.counter = len(self.topology)

    # @set_ev_cls(EventCalculateDropRate)
    # def calculate_drop_rate_on_link(self, ev): 
    #     for (src_dpid, src_port) in self.link_stats_history.keys(): 

    #         l = self.link_stats_history[(src_dpid, src_port)]
    #         dst_dpid = l['dst_dpid']
    #         dst_port = l['dst_port']

    #         drop_rate = (l['tx_at_src'] - l['rx_at_dst'])  / l['bw'] if l['bw'] != 0 else 0
    #         # push data to DB onif data has varied  
    #         if drop_rate != l.get('drop_rate', 0) and drop_rate > 0: 
    #             data = [
    #                     {
    #                         "fields": {
    #                             "drop_rate": round(drop_rate, 2) 
    #                             },
    #                         "tags": {
    #                             "src_dpid": src_dpid, 
    #                             "dst_dpid": dst_dpid, 
    #                             "src_port" : src_port, 
    #                             "dst_port" : dst_port
    #                             },
    #                         "measurement": "link_drop_rate"
    #                     }
    #                 ]
    #             # write(data)
    #         l['drop_rate'] = drop_rate



    '''
    register new switch 
    add table-miss rule 
    '''
    @set_ev_cls(ofp_event.EventOFPMsgBase, CONFIG_DISPATCHER)
    def switch_initer(self, ev):
        msg = ev.msg
        datapath = ev.msg.datapath
        # register dpid 
        self.datapaths['%016x' % datapath.id] = datapath
        # ofproto = datapath.ofproto
        # parser = datapath.ofproto_parser
        # match = parser.OFPMatch()
        # """
        # table miss actions, tell switch to: 
        # (1) no buffer for packet payload
        # (2) send packet to controller if it does not know where to forward 
        # """
        # actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
        #                                   ofproto.OFPCML_NO_BUFFER)]
        # self.add_flow_rule(datapath, 0, match, actions)


    '''
    port state change handler 
    register new switch 
    delete dead switch 
    '''

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                # self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths['%016x' % datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                # self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths['%016x' % datapath.id]
