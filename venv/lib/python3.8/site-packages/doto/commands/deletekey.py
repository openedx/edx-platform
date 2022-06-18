'''
create a new sshkey
'''
from __future__ import print_function
from doto import connect_d0
from doto.errors import ShowHelp

def main(args):
    d0 = connect_d0()

    ssh_key_id = args.key_id
    _ = d0.delete_key_pair(ssh_key_id=ssh_key_id)

def add_parser(subparsers):
    parser = subparsers.add_parser('deletekey',
                                      help="Delete key from digital ocean",
                                      description=__doc__)


    parser.add_argument(dest="key_id",type=int,
                                      action="store", default=None)

    parser.set_defaults(main=main, sub_parser=parser)
