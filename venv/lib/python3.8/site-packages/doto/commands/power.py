'''

power on/off a droplet

e.g:
doto power-off Random

'''

from __future__ import print_function
from doto import connect_d0

def power_on(args):
    d0 = connect_d0()
    try:
        droplet = d0.get_droplet(int(args.droplet_name))
    except ValueError:
        droplet = d0.get_droplet_by_name(args.droplet_name)

    e = droplet.power_on()
    
    print("Powering On")
    if args.wait: 
        e.wait(callback=print_callback)
        print("Finished")
    else:
        print("Event %s" % e.event_id)

def print_callback(wait_status, event):
    print("Waiting for status to be %s (got %s) at %s%%" % (wait_status, event.status, event.data.get('percentage') or 0)) 
    
def power_off(args):
    d0 = connect_d0()
    try:
        droplet = d0.get_droplet(int(args.droplet_name))
    except ValueError:
        droplet = d0.get_droplet_by_name(args.droplet_name)

    e = droplet.power_off()
    
    print("Powering Off")
    if args.wait: 
        e.wait(callback=print_callback)
        print("Finished")
    else:
        print("Event %s" % e.event_id)


def add_parser(subparsers):
    parser = subparsers.add_parser('power-on',
                                      help="Power on droplet",
                                      description=__doc__)
    parser.add_argument("droplet_name", help="droplet name or droplet id")
    parser.set_defaults(main=power_on, sub_parser=parser)

    parser = subparsers.add_parser('power-off',
                                      help="Power off droplet",
                                      description=__doc__)
    parser.add_argument("droplet_name", help="droplet name or droplet id")
    parser.set_defaults(main=power_off, sub_parser=parser)

