'''

Terminate a droplet

'''

from __future__ import print_function
from doto import connect_d0
from doto.errors import ShowHelp

def main(args):
    d0 = connect_d0()

    id = args.droplet_id
    droplet = d0.get_droplet(id=id)
    droplet.destroy()


def add_parser(subparsers):
    parser = subparsers.add_parser('terminate',
                                      help="Destroy droplet from Digital Ocean",
                                      description=__doc__)


    parser.add_argument(dest="droplet_id",type=int,
                                      action="store", default=None)

    parser.set_defaults(main=main, sub_parser=parser)
