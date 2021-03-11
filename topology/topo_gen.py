import argparse
import json
import time

from mininet.cli import CLI
from mininet.link import OVSLink, TCLink
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController, Switch
from mininet.topo import Topo

import auto_test

parser = argparse.ArgumentParser(description = "generate mininet topology")
parser.add_argument('--gf', type = str, default = 'testbed.json', help = 'topology file path')
parser.add_argument('--test', type = str, default = 'disable')
args = parser.parse_args()

# parse json file 
def read_topo_file(path) : 
    with open(path) as json_file: 
        topo_config = json.load(json_file)
    return topo_config 


class Topology(Topo) : 
    def __init__(self, topo_info):
        super().__init__(self)

        # parse configruation parameters 
        self.topo_info = topo_info
        self.links_info = topo_info['links']
        self.hosts_info = topo_info['hosts']
        self.switches_info = topo_info['switches']

        # node_name : str -> node : Node
        self.nodes_dict = {}

        # add network entities 
        self.add_hosts(self.hosts_info)
        self.add_switches(self.switches_info)
        self.add_links(self.links_info)

    def add_switches(self, switches) : 
        for switch in switches: 
            self.nodes_dict[switch]  = self.addSwitch(
                name = switch, 
                dpid = switches[switch]["dpid"]
                )
    
    def add_hosts(self, hosts) :
        for host in hosts : 
            self.nodes_dict[host] = self.addHost(
                name = host, 
                ip = hosts[host]['ip'], 
                mac = hosts[host]['mac']
            )

    def add_links(self, links) : 
        for link in links : 
            self.addLink(
                self.nodes_dict[link[0]], 
                self.nodes_dict[link[1]], 
                cls = TCLink, 
                **link[2]
                )


# controller creating 
def create_controller(controller_info) : 
    controller_name = controller_info['controller_name']
    controller_ip = controller_info['controller_ip']
    controller_port = controller_info['controller_port'] 
    return RemoteController(
        name = controller_name, 
        ip = controller_ip, 
        port = controller_port
    )


# emulate mininet topo
def create_net(topo, ctrl = None, if_static_mac = False, if_auto_arp = False) : 
    return Mininet(
        topo = topo, 
        switch = OVSSwitch, 
        controller = ctrl, 
        autoSetMacs = if_static_mac, 
        autoStaticArp = if_auto_arp, 
        link = OVSLink
    )


def main() : 
    # parse global info
    global_info = read_topo_file(args.gf)
    topo_info = global_info['topo_info']
    hosts_info = topo_info['hosts']
    client_list = []
    server_list = []

    controller_info = global_info['controller_info']

    # create topology, controller, network 
    newtopo = Topology(topo_info)
    ctrl = create_controller(controller_info)
    # set auto_arp, because we do not have a smart controller yet :( 
    net = create_net(newtopo, ctrl, if_auto_arp = False)
    net.start()
    
    # filter client and server out 
    for host in hosts_info:
        host = net.get("%s" %(host))
        if ("%s" %(host)).find("client") > -1:
            client_list.append(host)
        elif ("%s" %host).find("server") > -1:
            server_list.append(host)
    time.sleep(1)
    '''
    all hosts ping a unexisted gateway after mininet is booted up 
    for TopologyDiscovery to locate the host 
    '''
    for client in client_list: 
        client.cmd('timeout 0.1 ping 10.0.0.254')
    for server in server_list: 
        server.cmd('timeout 0.1 ping 10.0.0.254')

    # choose to launch auto test or CLI 
    if args.test == "enable":
        auto_test.auto_test(net, topo_info)
    else:
        CLI(net)

if __name__ == '__main__' : 
    main()
