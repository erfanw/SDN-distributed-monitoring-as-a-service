import base64
import json
import time
from threading import Timer

import eventlet
import networkx as nx
import numpy
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import (CONFIG_DISPATCHER, DEAD_DISPATCHER,
                                    MAIN_DISPATCHER, set_ev_cls)
from ryu.lib import hub
from ryu.lib.packet import ether_types, ethernet, ipv4, packet, udp
from ryu.ofproto import ether, ofproto_v1_3
from ryu.ofproto.ofproto_v1_3_parser import OFPFlowStatsReply

from event import EventTopoUpdate


class LinkCapacityMeasurement(app_manager.RyuApp):

    _EVENTS = [
        EventTopoUpdate
    ]

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *_args, **_kwargs):
        super().__init__(*_args, **_kwargs)
        self.datapaths = {}
        self.topo = nx.DiGraph()
        self.curr_on = None
        '''
        store switch statistics history 
        dpid : {
            old_time_stamp : 
            old_bytes_count : 
            old_link_cap : 
        }
        '''
        self.flow_stats_history = {}
        '''
        store link capcity 
        looks like: 
        {
            sw1 : {
                sw2 : link_cap1, 
                sw3 : link_cap2
                ... 
            }
        }
        '''
        self.link_cap = {}
        self.query = None
        # read dummy playload from txt 
        with open('dummy_payload', 'r') as txt_file: 
            self.payload = bytes(txt_file.read(), 'UTF-8') 
    
    # this thread is for updating topo 
    @set_ev_cls(EventTopoUpdate)
    def start_query_thread(self, ev):         
        link_list = ev.topology
        for link in link_list: 
            self.topo.add_edge(
                link['src_dpid'], 
                link['dst_dpid'],
                src_port = link['src_port'], 
                dst_port = link['dst_port']
            )
        # lanuch query thread if it hasn't been after topo info initialized 
        if self.query == None: 
            self.query = hub.spawn(self.query_thread)

    # this thread is inteneded to impose each switch flood pkt to its neighbors 
    def query_thread(self): 
        for dp in self.datapaths: 
            self.curr_on = dp
            src = self.datapaths[dp]
            # generate upd pkt 
            out = self.pkt_out_generator(src)
            # a timer, set loop interval 
            t = RepeatingTimer(1, self.query_neigh_port_statistics, (src, ))
            t.start()
            # every 10s 
            with eventlet.Timeout(10, False): 
                self.send_pk_from_to(src)
            t.cancel()
            for dp in self.flow_stats_history:
                self.flow_stats_history[dp]['old_link_cap'] = 0
            
        # after querying all switch, output the data to a .json file
        json_str = json.dumps(self.link_cap)
        with open('link_cap.json', 'w') as json_file: 
            json_file.write(json_str)

        self.logger.info('link capacity measurement is done')
        hub.sleep(1000)
        return

    # send upd pkt to switch src
    def send_pk_from_to(self, src): 
        out = self.pkt_out_generator(src)
        while True: 
            src.send_msg(out)
    # query neighbors' port stats 
    def query_neigh_port_statistics(self, src): 
        # get adjacent nodes from topo
        adjs = self.topo.neighbors('%016x' % src.id)
        # iterate the adjacent list and make query 
        for adj in adjs: 
            adj_datapath = self.datapaths[adj]
            parser = adj_datapath.ofproto_parser
            ofproto = adj_datapath.ofproto
            # set match file 
            match = parser.OFPMatch(eth_src = 'ff:ff:ff:ff:ff:ff')
            # parse request pkt 
            req = parser.OFPFlowStatsRequest(adj_datapath, match = match)
            adj_datapath.send_msg(req)

    # this thread is intended to generating pkt_out 
    def pkt_out_generator(self, src): 
        # fectch an udp pkt 
        pkt = self.upd_pkt_generator()
        pkt.serialize()
        data = pkt.data
        parser = src.ofproto_parser
        ofproto = src.ofproto
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        # parse a pkt_out message
        out = parser.OFPPacketOut(
            datapath = src, 
            buffer_id = ofproto_v1_3.OFP_NO_BUFFER, 
            in_port = ofproto.OFPP_CONTROLLER, 
            actions = actions, 
            data = data
        )
        return out
    
    # generate udp pkt 
    def upd_pkt_generator(self): 
        pkt = packet.Packet()
        eth_header = ethernet.ethernet(
            ethertype=ether.ETH_TYPE_IP, 
            src='ff:ff:ff:ff:ff:ff', 
            dst='ff:ff:ff:ff:ff:ff'
        )
        ip_header = ipv4.ipv4(
            src='1.1.1.1', 
            dst='1.1.1.1'
        )
        udp_header = udp.udp()
        pkt.add_protocol(eth_header)
        pkt.add_protocol(ip_header)
        pkt.add_protocol(udp_header)
        pkt.add_protocol(self.payload)
        return pkt

    # handle flow stats 
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_handler(self, ev): 
        dpid = ev.msg.datapath.id
        flows = ev.msg.body 
        for flow in flows: 
            # fetch history for this calculation round 
            old_timestamp = self.flow_stats_history['%016x' % dpid]['old_timestamp']
            old_bytes_count = self.flow_stats_history['%016x' % dpid]['old_bytes_count']
            # print(old_bytes_count)
            # calculate timestamp 
            new_timestamp = flow.duration_sec + flow.duration_nsec * 10 ** (-9)
            new_bytes_count = flow.byte_count 
            # calculate capacitt 
            link_capcity = ((new_bytes_count - old_bytes_count) / (new_timestamp - old_timestamp)) * 10 ** (-6) * 8
            self.logger.info('the %s ---> %s, the capacity is %s', self.curr_on, dpid, link_capcity)

            # if the stats is stable 
            if (self.flow_stats_history['%016x' % dpid]['old_link_cap'] - link_capcity) < link_capcity * (0.05): 
                self.link_cap[self.curr_on]['%016x' % dpid] = link_capcity

            # keep stats in a dict 
            self.flow_stats_history['%016x' % dpid]['old_bytes_count'] = new_bytes_count
            self.flow_stats_history['%016x' % dpid]['old_timestamp'] = new_timestamp
            self.flow_stats_history['%016x' % dpid]['old_link_cap'] = link_capcity

    # update connected switch if new switch comes in or leave 
    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.datapaths['%016x' % datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                del self.datapaths['%016x' % datapath.id] 

        # initialize the history 
        self.flow_stats_history['%016x' % datapath.id] = {}
        self.flow_stats_history['%016x' % datapath.id]['old_timestamp'] = 0
        self.flow_stats_history['%016x' % datapath.id]['old_bytes_count'] = 0
        self.flow_stats_history['%016x' % datapath.id]['old_link_cap'] = 0
        self.link_cap['%016x' % datapath.id] = {}
        
        # install drop rule onto every switch 
        self.install_drop_rule(datapath)

    def install_drop_rule(self, datapath):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch(eth_src = 'ff:ff:ff:ff:ff:ff')
        # simply drop if actions is empty 
        actions = []
        self.add_flow(datapath, 0, match, actions)

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

# a repeating timer for better flow control 
class RepeatingTimer(Timer): 
    def run(self): 
        while not self.finished.is_set():
            self.function(*self.args, **self.kwargs)
            self.finished.wait(self.interval)