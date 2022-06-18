'''

List all Images

'''

from __future__ import print_function, division, absolute_import
from doto import connect_d0


def main(args):
    d0 = connect_d0()
    _ = d0.get_all_images(table=True)

def add_parser(subparsers):
    parser = subparsers.add_parser('listimages',
                                      help='list all images',
                                      description=__doc__)

    parser.set_defaults(main=main, sub_parser=parser)
