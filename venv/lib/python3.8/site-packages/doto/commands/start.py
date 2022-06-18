'''

Create a Droplet

eg:
doto start --name Random --size_id 66 --image_id 2158507 --region_id 1 --ssh_key_ids 89221

'''

from __future__ import print_function, division, absolute_import
from doto import connect_d0

def main(args):
    d0 = connect_d0()


    name = args.name
    size_id = args.size_id
    image_id = args.image_id
    region_id = args.region_id
    ssh_keys = args.ssh_key_ids

    #convert ssh_keys to list of ints
    ssh_keys = ssh_keys.split(',')
    ssh_key_ids = [int(key) for key in ssh_keys]

    d0.create_droplet(name=name,size_id=size_id,
                      image_id=image_id,region_id=region_id,
                      ssh_key_ids=ssh_key_ids,)

def add_parser(subparsers):
    parser = subparsers.add_parser('start',
                                      help='create a droplet or cluster of droplets',
                                      description=__doc__)

    parser.add_argument("-n", "--name", dest="name",
                                      action="store", default=None,
                                      required=True)

    parser.add_argument("-s", "--size_id", dest="size_id",type=int,
                                      action="store", default=None,
                                      required=True)

    parser.add_argument("-i", "--image_id", dest="image_id",type=int,
                                      action="store", default=None,
                                      required=True)

    parser.add_argument("-r", "--region_id", dest="region_id",type=int,
                                      action="store", default=None,
                                      required=True)

    parser.add_argument("-k", "--ssh_key_ids", dest="ssh_key_ids",
                                      action="store", default=None,help='comma separated ints',
                                      required=True)


    parser.set_defaults(main=main, sub_parser=parser)

