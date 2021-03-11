
from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls

import event

# class TopoBase(Switches): 

#     def __init__(self, *_args, **_kwargs):
#         super(TopoBase, self).__init__(*_args, **_kwargs)
#         self.name = 'topobase'

#     @set_ev_cls(EventHaltLLDP)
#     def shut_lldp(self, ev): 
#         self.close()

def get_host(app, dpid=None):
    rep = app.send_request(event.EventHostRequest(dpid))
    return rep.hosts

def get_link(app, dpid=None):
    rep = app.send_request(event.EventLinkRequest(dpid))
    return rep.links

def get_switch(app, dpid=None):
    rep = app.send_request(event.EventSwitchRequest(dpid))
    return rep.switches


# app_manager.require_app('topodsc_base', api_style=True)
# app_manager.require_app('ryu.topology.switches', api_style=True)
