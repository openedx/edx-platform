'''

Info of a droplet

eg:
doto info droplet_name ip_address

'''

from __future__ import print_function
from doto import connect_d0
import sys
from doto.event import Event

def print_callback(wait_status, event):
    print("Waiting for status to be %s (got %s) at %s%%" % (wait_status, event.status, event.data.get('percentage') or 0)) 
    
    
def main(args):
    d0 = connect_d0()
    e = Event(d0._conn, args.event_id)
    
    print("Event %s" % e)
    if args.wait: 
        e.wait(callback=print_callback)
        print("Finished")
        

def add_parser(subparsers):

    parser = subparsers.add_parser('event',
                                      help="Get droplet status",
                                      description=__doc__)
    parser.add_argument("event_id", type=int)
    parser.set_defaults(main=main, sub_parser=parser)
