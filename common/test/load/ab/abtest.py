#!/usr/bin/env python

"""
A script to run some ab load tests.
"""
import os
import sys
import argparse



"""
function bench {


    set -e

    set -x

    NAME=$1

    REQUESTS=$2

    CONCURRENT=$3

    PAGE=$4

    OPTS=$5


    OUTDIR="$NAME/page_${PAGE//\//-}"

    mkdir -p $OUTDIR

    ab -Aanant:agarwal -n $REQUESTS -c $CONCURRENT $OPTS http://prod-edx-001.m.edx.org$PAGE | tee -- $OUTDIR/$REQUESTS-$CONCURRENT.results


    set +ex

}


For loop to ramp up load:

for conc in 1 2 3 5 8 13 21; do bench anon ${conc}00 $conc /jobs; done

Useful curl incantation:

curl stage-edx-001.m.edx.org/courses/BerkeleyX/CS188/fa12/courseware/Week_1/Project_0_Tutorial/ -b "sessionid=de0fe775b2192445dce76a09deeb740a;csrftoken=2987de2837f3d7051a9d92335b448cf1" -u "anant:agarwal" -D headers

pass cookies, user/pass, and dump headers to file "headers"

"""

def test_url(url, requests, concurrency, ab_options, logpath):
    """
    Run tests for a url
    """

    cmd = "ab -n {requests} -c {concurrency} {opts} {url} | tee -- {log}".format(requests=requests,
                                                                  concurrency=concurrency,
                                                                  url=url,
                                                                  opts=ab_options,
                                                                  log=logpath,)
    print "running {0}".format(cmd)
    os.system(cmd)

def read_pagelist(filepath):
    """
    read list of pages, skipping blank lines and lines that start with '#'
    """
    out = []
    try:
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or len(line) == 0:
                    continue
                out.append(line)
    except:
        print "Couldn't load {0}".format(filepath)
        raise
    return out



def loadtest(args):
    """Actually do the load test

    args: argparse result.  Should contain:

    server: url of server, with or without http[s]://
    pages: list of page urls, including leading slash
    abopts: list of options to pass to ab.
    """
    server = args.server
    name = args.name
    ab_options = args.abopt if args.abopt else []
    ab_options.append("-Aanant:agarwal")

    cookies = []
    if args.sessionid:
        cookies.append("sessionid={0}".format(args.sessionid))

    if args.csrftoken:
        cookies.append("csrftoken={0}".format(args.csrftoken))

    if len(cookies) > 0:
        cookie_str = "; ".join(cookies)
        ab_options.append("-C '{0}'".format(cookie_str))

    pages = args.pages if args.pages else []
    if args.pagelist:
        pages += read_pagelist(args.pagelist)

    if not server.startswith('http'):
        # use http by default, but if https is specified, use that
        server = 'http://' + server

    # want a string
    ab_options = ' '.join(str(s) for s in ab_options) if ab_options is not None else ""

    # If there are already results for this run, just delete them.  (TODO: Desired behavior?)
    os.system("rm -rf {name}".format(name=name))
    for page in pages:
        url = "{server}{page}".format(server=server, page=page)
        outdir = "{name}/page_{page}".format(name=name, page=page.replace('/', '-'))
        print "Testing {0}. Output in {1}".format(url, outdir)
        os.makedirs(outdir)
        for conc in args.concurrency:
            requests = conc * args.reqs_per_thread
            logpath = outdir + '/{requests}-{conc}.results'.format(requests=requests, conc=conc)
            test_url(url, requests, conc, ab_options, logpath)

def main():
    """
    Run tests

    machine: load-test-001.m.edx.org
    elb: load-test.edx.org
    """

    parser = argparse.ArgumentParser(description='Run load tests on an edx server.')
    parser.add_argument('server',
                        help='the server to test')
    parser.add_argument('--pages', metavar='PAGE', type=str, nargs='*',
                        help='a page to test (url will be server/{PAGE})')
    parser.add_argument('--sessionid',
                        help='if testing non-anonymously, specify session id')
    parser.add_argument('--csrftoken',
                        help='if posting forms, specify csrftoken')
    parser.add_argument('-c', dest='concurrency', action='append', type=int, default=[1],
                        help="try this number of simultaneous threads.  May be specified more than once.")
    parser.add_argument('-r', type=int, default=2, help="Number of requests per thread", dest='reqs_per_thread')

    parser.add_argument('--name',
                        help='test name--results will be in {name}/',
                        default='noname')
    parser.add_argument('--pagelist',
                        help="""a file containing additional pages to test.
Empty lines and lines that start with # are ignored.
Will be added to pages specified on the command line""")

    parser.add_argument('--abopt', action='append')
    args = parser.parse_args()

    loadtest(args)

if __name__ == "__main__":
    main()
