'''

List all Droplets

'''

from __future__ import print_function, division, absolute_import
from doto import connect_d0


def main(args):
    d0 = connect_d0()

    if args.droplet_id:
        data  = d0.get_droplet(args.droplet_id,raw_data=True)
        d0._pprint_table([data['droplet']])

    else:
        d0.get_all_droplets(table=True)

def add_parser(subparsers):
    parser = subparsers.add_parser('listdroplets',
                                      help='list all droplets',
                                      description=__doc__)
    parser.add_argument("-id", "--droplet_id", dest="droplet_id",type=int,
                                      action="store", default=None)

    parser.set_defaults(main=main, sub_parser=parser)
