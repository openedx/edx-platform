""" Command line interface to difflib.py to compare html files
"""

import sys, os, time, difflib, optparse, os.path, re
from urllib import unquote_plus

def main():
     # Configure the option parser
    usage = "usage: %prog fromdir todir"
    parser = optparse.OptionParser(usage)
    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        sys.exit(1)
    if len(args) != 2:
        parser.error("need to specify both a fromdir and todir")

    fromdir, todir = args # as specified in the usage string

    if not os.path.isdir(fromdir):
        print "'%s' is not a directory" % fromdir

    if not os.path.isdir(todir):
        print "'%s' is not a directory" % todir

    from_files = os.listdir(fromdir)
    to_files = os.listdir(todir)

    for filename in from_files:
        if filename in to_files:

            fromfile = os.path.join(fromdir, filename)
            tofile = os.path.join(todir, filename)

            # we're passing these as arguments to the diff function
            # fromdate = time.ctime(os.stat(fromfile).st_mtime)
            # todate = time.ctime(os.stat(tofile).st_mtime)
            fromlines = cleanup(open(fromfile, 'U').readlines())
            tolines = cleanup(open(tofile, 'U').readlines())

            diff = difflib.unified_diff(fromlines, tolines, fromdir, todir, n=0)
                                    # fromdate, todate, n=0)

            print 'FILE: %s' % unquote_plus(filename)
            # we're using writelines because diff is a generator
            sys.stdout.writelines(diff)
            print ''

def cleanup(lines):

    lines = [s.replace('/c4x/MITx/6.002x/asset', '/static/content-mit-6002x') for s in lines]
    lines = [s.replace('handouts_', 'handouts/') for s in lines]
    return lines

if __name__ == '__main__':
    main()