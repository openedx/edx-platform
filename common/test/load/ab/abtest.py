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


def loadtest(server, pages, ab_options, args):
    """Actually do the load test

    server: url of server, with or without http[s]://
    pages: list of page urls, including leading slash
    ab_options: list of options to pass to ab.
    args: dictionary of other random arguments
    """
    if not server.startswith('http'):
        # use http by default, but if https is specified, use that
        server = 'http://' + server

    # want a string
    ab_options = ' '.join(str(s) for s in ab_options) if ab_options is not None else ""

    reqs_per_thread = 10
    name = args.get('name', "noname")
    for page in pages:
        url = "{server}{page}".format(server=server, page=page)
        outdir = "{name}/page_{page}".format(name=name, page=page.replace('/', '-'))
        os.makedirs(outdir)
        for conc in [1]: #[1, 2, 3, 10]:
            requests = conc * reqs_per_thread
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
    parser.add_argument('pages', metavar='PAGE', type=str, nargs='+',
                        help='a page to test (url will be server/{PAGE})')
    parser.add_argument('--sessionid',
                        help='if testing non-anonymously, specify session id')

    parser.add_argument('--abopt', action='append')
    args = parser.parse_args()

    loadtest(args.server, args.pages, args.abopt, vars(args))

if __name__ == "__main__":
    main()
