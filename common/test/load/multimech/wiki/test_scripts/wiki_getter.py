import random
import time
import requests
import random

# NOTE: Script relies on this user being signed up for cs188, and cs188 having started.
email = 'victor+test@edx.org'
password = 'abc123'

machine = 'load-test-001.m.edx.org'
protocol = 'http://'

auth = ('anant', 'agarwal')

def url(path):
    """
    path should be something like '/', '/courses'
    """
    return ''.join([protocol, machine, path])


class Transaction(object):
    def __init__(self):
        # Load / to get csrf cookie
        s = requests.session(auth=auth)
        r = s.get(url('/'))
        #print 'initial resp headers: ', r.headers
        #print 'initial cookies: ', s.cookies

        # Need to set the header as well as the cookie.  Why? No one knows.
        headers = {'X-CSRFToken' : s.cookies['csrftoken']}
        # login
        r = s.post(url('/login'), data={'email' : email, 'password': password}, headers=headers)
        print r.text
        #print 'login req headers',  r.request.headers
        #print 'login resp headers',  r.headers
        #print 'status code: ', r.status_code
        #        assert r.status_code == requests.codes.ok
        #print "cookies: {0}".format(r.cookies)
        self.session = s

    def run(self):

        s = self.session
        # r = s.get(url('/'))
        # # requests magically follows redirects, so we expect a 200
        # print r.status_code
        # assert r.status_code == requests.codes.ok
        # r.raw.read()

        # And now get the page again

        r = s.get(url('/courses/BerkeleyX/CS188/fa12/wiki/CS188/_dir'))
        assert r.status_code == requests.codes.ok
        r.raw.read()


if __name__ == '__main__':
    trans = Transaction()
    print "running..."
    trans.run()
    print "run done"
