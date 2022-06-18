'''

list images by name

'''

from __future__ import print_function
from doto import connect_d0

def main(args):
    
    d0 = connect_d0()
    for image_name in args.image_names:
        image = d0.get_image_by_name(image_name)
        if image is None and args.fail_fast:
            raise Exception("Image %s does not exist" % image_name)
        elif image is None:
            print("Image %s does not exist" % image_name)
            continue
        
        if args.action == 'show':
            print(image)
        elif args.action == 'destroy':
            image.destroy()
            print('Image %s destroyed' % (image.id))
    
    
def add_parser(subparsers):
    parser = subparsers.add_parser('image',
                                      help="Image",
                                      description=__doc__)
    parser.add_argument("image_names", nargs='+')
    parser.add_argument("-a", "--action", choices=['show', 'destroy'], default='show')
    parser.add_argument("-f", "--fail-fast", action='store_true', help='fail if ')
    
    
    parser.set_defaults(main=main, sub_parser=parser)

