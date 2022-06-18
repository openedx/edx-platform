'''

Info of a droplet

eg:
doto info droplet_name ip_address

'''

from __future__ import print_function
from doto import connect_d0
import sys

        
def main(args):
    d0 = connect_d0()
    try:
        droplet = d0.get_droplet(int(args.droplet_name))
    except ValueError:
        droplet = d0.get_droplet_by_name(args.droplet_name)

    sys.stdout.write(str(getattr(droplet, args.attr)))

def add_parser(subparsers):

    parser = subparsers.add_parser('info',
                                      help="Get droplet status",
                                      description=__doc__)
    parser.add_argument("droplet_name", help="droplet name or droplet id")
    parser.add_argument("attr")
    parser.set_defaults(main=main, sub_parser=parser)
