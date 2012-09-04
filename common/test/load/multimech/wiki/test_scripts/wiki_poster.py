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


pages_to_get = ['/courses/BerkeleyX/CS188/fa12/wiki/CS188/',
                '/courses/BerkeleyX/CS188/fa12/wiki/CS188/_edit/',
                '/courses/BerkeleyX/CS188/fa12/wiki/CS188/_dir/',
                '/courses/BerkeleyX/CS188/fa12/wiki/CS188/_create/',
                ]

def randstr(len, chrs='abcdef123456 '):
    return ''.join(random.choice(chrs) for r in range(len))

def randslug(len):
    # same as random string, but without spaces
    return randstr(len, chrs='abcdef123456')

def wiki_post_data():
    """Return the POST data for a random wiki post"""
    title = randstr(40)
    slug = randslug(20)
    content = randstr(200)
    summary = randstr(20)

    return {'title': title,
            'slug': slug,
            'content': content,
            'summary': summary,
            'save_changes':''}

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

    def create_article(self):
        s = self.session
        headers = {'X-CSRFToken' : s.cookies['csrftoken']}
        r = s.post(url('/courses/BerkeleyX/CS188/fa12/wiki/CS188/_create/'), data=wiki_post_data(), headers=headers)
        assert r.status_code == requests.codes.ok
        r.raw.read()

    def run(self):
        s = self.session
        # r = s.get(url('/'))
        # # requests magically follows redirects, so we expect a 200
        # print r.status_code
        # assert r.status_code == requests.codes.ok
        # r.raw.read()

        self.create_article()
        # And now get the page again
        r = s.get(url('/courses/BerkeleyX/CS188/fa12/wiki/CS188/_dir/'))
        assert r.status_code == requests.codes.ok


if __name__ == '__main__':
    trans = Transaction()
    print "running..."
    trans.run()
    print "run done"
