'''
create a new sshkey
'''
from __future__ import print_function
from doto import connect_d0
from doto.errors import ShowHelp

def main(args):
    d0 = connect_d0()
    print(args.output_file)
    print(args.dry_run)

    if not args.output_file:
        print("Please provide a key name")
        raise ShowHelp()

    ssh_key_name = args.output_file
    d0.create_key_pair(ssh_key_name=ssh_key_name,cli=True,
                       dry_run=args.dry_run)

def add_parser(subparsers):
    parser = subparsers.add_parser('createkey',
                                      help="Save the new keypair to a file",
                                      description=__doc__)


    parser.add_argument("-o", "--output-file", dest="output_file",
                                      action="store", default=None)

    parser.add_argument("-d", "--dry-run",
                        help="create the key but do not upload",
                        action="store_true")

    parser.set_defaults(main=main, sub_parser=parser)
