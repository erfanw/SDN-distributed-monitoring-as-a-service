
import copy

from networkx.exception import NetworkXError
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (CONFIG_DISPATCHER, DEAD_DISPATCHER,
                                    MAIN_DISPATCHER, set_ev_cls)
from ryu.lib import hub
from ryu.lib.packet import ether_types, ethernet, packet
from ryu.ofproto import ofproto_v1_3

from event import EventHaltLLDP, EventHostInfoUpdate, EventTopoUpdate
from topodsc_api import get_host, get_link, get_switch


class TopologyDiscovery(app_manager.RyuApp):  

    _EVENTS = [
        EventTopoUpdate, 
        EventHostInfoUpdate, 
        EventHaltLLDP
    ]

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    def __init__(self, *_args, **_kwargs):
        super().__init__(*_args, **_kwargs)
        self.topo_link_list = []
        self.topo_sw_list = []
        self.topo_host_dict = {}
        self.threads.append(hub.spawn(self.host_updater))
        self.threads.append(hub.spawn(self.topo_updater)) 
        
    
    def topo_updater(self): 
        hub.sleep(10)
        while True: 
            topo_raw_links = []
            topo_raw_switch = []
            topo_raw_links = copy.copy(get_link(self, None))
            topo_raw_switch = copy.copy(get_switch(self, None))
            # convert raw switch objects into dict 
            self.topo_sw_list = []
            for s in topo_raw_switch: 
                switch_info = s.to_dict()
                '''
                switch_info looks like: 
                    {
                        'dpid': '0000000000000006', 
                        'ports': [
                            {'dpid': '0000000000000006', 'port_no': '00000001', 'hw_addr': 'f2:70:53:a9:62:5f', 'name': 's4-eth1'}, 
                            {'dpid': '0000000000000006', 'port_no': '00000002', 'hw_addr': '4e:e9:95:ea:68:00', 'name': 's4-eth2'}, 
                            {'dpid': '0000000000000006', 'port_no': '00000003', 'hw_addr': '06:d6:de:e1:82:3b', 'name': 's4-eth3'}
                        ]
                    }
                '''
                self.topo_sw_list.append(switch_info)
            # conver raw link objects into dict 
            self.topo_link_list = []
            for l in topo_raw_links: 
                link_info = l.to_dict()
                # print(link_info)
                '''
                link_info looks like: 
                {
                    'src': {'dpid': '0000000000000004', 'port_no': '00000002', 'hw_addr': 'ba:f9:b6:04:2b:1e', 'name': 's2-eth2'}, 
                    'dst': {'dpid': '0000000000000007', 'port_no': '00000003', 'hw_addr': '66:9f:ff:51:cb:47', 'name': 'oz1-eth3'}
                }
                '''
                self.topo_link_list.append({
                    'src_dpid' : link_info['src']['dpid'], 
                    'src_port' : link_info['src']['port_no'], 
                    'dst_dpid' : link_info['dst']['dpid'], 
                    'dst_port' : link_info['dst']['port_no']
                })
            self.send_event_to_observers(EventTopoUpdate(self.topo_link_list))
            self.send_event_to_observers(EventHaltLLDP())
            hub.sleep(90)

    '''
    periodically query host information, in a passive fashion 
    # TODO : plan to be replaced by a proactive host prober
    '''
    def host_updater(self): 
        hub.sleep(10)
        while True: 
            # TODO : plan to be replaced by the host updater 
            topo_raw_host = copy.copy(get_host(self, None))
            self.topo_host_dict = {}
            for h in topo_raw_host: 
                host_info = h.to_dict()
                '''
                host_info['port'] looks like: 
                {
                    'dpid': dpid_to_str(self.dpid), # the dpid of the switch that connects to the host 
                    'port_no': port_no_to_str(self.port_no), # the port no of the port that faces the host 
                    'hw_addr': self.hw_addr, # the port mac 
                    'name': self.name.decode('utf-8')
                }
                '''
                self.topo_host_dict[host_info['mac']] = {
                    'ipv4' : host_info['ipv4'], 
                    'port' : host_info['port']
                }
            self.send_event_to_observers(EventHostInfoUpdate(self.topo_host_dict))
            hub.sleep(5)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod) 

        
