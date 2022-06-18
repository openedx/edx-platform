'''

Terminate a droplet

'''

from __future__ import print_function
from doto import connect_d0

def rebuild(args):
    
    d0 = connect_d0()
    droplet = d0.get_droplet_by_name(args.droplet_name)
    
    if args.image:
        try:
            image_id = int(args.image)
        except ValueError:
            image_id = d0.get_image_by_name(args.image)
    else:
        image_id = droplet.image_id
            
    e = droplet.rebuild(image_id)
    
    print("Rebuild Droplet")
    if args.wait: 
        e.wait(callback=print_callback)
        print("Finished")
    else:
        print("Event %s" % e.event_id)
    
def print_callback(wait_status, event):
    print("Waiting for status to be %s (got %s) at %s%%" % (wait_status, event.status, event.data.get('percentage') or 0)) 
    
        
def add_parser(subparsers):
    parser = subparsers.add_parser('rebuild',
                                      help="Rebuild a droplet",
                                      description=__doc__)
    parser.add_argument("droplet_name")
    parser.add_argument('-i','--image')
    
    parser.set_defaults(main=rebuild, sub_parser=parser)

