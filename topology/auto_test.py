import os
import random
import time

from mininet.cli import CLI
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController, Switch
from mininet.topo import Topo


def iperf(client, server, port, bw) :
    print("iperf test between %s and %s" %(client, server))
    client.cmd('iperf -c %s -p %s -b %s -d -t 1000 -u &' %(server.IP(), port, bw*1000000))

def iperf_tcp(client, server, port, bw) :
    print("iperf test between %s and %s" %(client, server))
    client.cmd('iperf -c %s -p %s -b %s -d -t 1000 &' %(server.IP(), port, bw*1000000))

def auto_test(net, topo_info) :
    hosts_info = topo_info['hosts']
    client_list = []
    server_list = []
    # print("Please wait for the controller to be initialized")
    time.sleep(10)
    for host in hosts_info:
        host = net.get("%s" %(host))
        if ("%s" %(host)).find("client") > -1:
            client_list.append(host)
        elif ("%s" %host).find("server") > -1:
            server_list.append(host)

    # for client in client_list:
    #     client.cmd("iperf -s -p 4443 -u &")
    #     client.cmd("iperf -s -p 4444 -u &")
    #     client.cmd("iperf -s -p 4445 -u &")
    #     client.cmd("iperf -s -p 4446 -u &")
    #     client.cmd("iperf -s -p 4447 -u &")

    # for server in server_list:
    #     server.cmd('iperf -s -p 5001 -u &')
    #     server.cmd('iperf -s -p 5002 -u &')
    #     server.cmd('iperf -s -p 5003 -u &')
    #     server.cmd('iperf -s -p 5004 -u &')
    #     server.cmd('iperf -s -p 5005 -u &')
    #     #server.cmd('iperf -s -p 4443 &')
    
    # for client in client_list:
    #     for i in range(4000, 4050):
    #         client.cmd("iperf -s -p %s -u &" %i)
        
    #     for i in range(4050, 4100):
    #         client.cmd("iperf -s -p %s &" %i)

    for server in server_list:
        for i in range(5000, 5150):
            server.cmd("iperf -s -p %s -u &" %i)

        for i in range(5150, 5200):
            server.cmd("iperf -s -p %s &" %i)

    ############### Tests for the Stanford topology ###############
    p = 5000
    for client in client_list:
        for server in server_list:
            for i in range(p, p+1):
                iperf(client, server, i, 0.15) 
                time.sleep(2) 
        p = p + 1
        time.sleep(1)
 
    ############### Tests for the simplified topology ###############      
    # time.sleep(2)
    # for i in range(0,4):
    #     for j in range(5000, 5010):
    #         #iperf(client_list[i], server_list[i], j, random.gauss(1, 0.1)) 
    #         iperf(client_list[i], server_list[i], j, 1) 
    #         time.sleep(0.2) 
    #     time.sleep(2)
    #     for j in range(5150, 5160):
    #         #iperf_tcp(client_list[i], server_list[i], j, random.gauss(1, 0.1)) 
    #         iperf_tcp(client_list[i], server_list[i], j, 1) 
    #         time.sleep(0.2) 
    #     time.sleep(2)

    time.sleep(1000)
    # client_list[0].cmd("mn -c")
    # net.stop()
