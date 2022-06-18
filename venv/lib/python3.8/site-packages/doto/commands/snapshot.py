'''

Terminate a droplet

'''

from __future__ import print_function
from doto import connect_d0

def main(args):
    
    d0 = connect_d0()
    droplet = d0.get_droplet_by_name(args.droplet_name)
    
    e = droplet.create_snapshot(args.image_name)
    
    print("Snapshot Droplet")
    if args.wait: 
        e.wait(callback=print_callback)
        print("Finished")
    else:
        print("Event %s" % e.event_id)
    
def print_callback(wait_status, event):
    print("Waiting for status to be %s (got %s) at %s%%" % (wait_status, event.status, event.data.get('percentage') or 0)) 
    
        
def add_parser(subparsers):
    parser = subparsers.add_parser('snapshot',
                                      help="Save snapshot of droplet",
                                      description=__doc__)
    parser.add_argument("droplet_name")
    parser.add_argument("image_name")
    
    parser.set_defaults(main=main, sub_parser=parser)

