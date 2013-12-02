# A simple script demonstrating how to have an external program post problem
# responses to an edx server.
#
# ***** NOTE *****
# This is not intended as a stable public API.  In fact, it is almost certainly
# going to change.  If you use this for some reason, be prepared to change your
# code.
#
# We will be working to define a stable public API for external programs.  We
# don't have have one yet (Feb 2013).


import requests
import sys
import getpass

def prompt(msg, default=None, safe=False):
    d = ' [{0}]'.format(default) if default is not None else ''
    prompt = 'Enter {msg}{default}: '.format(msg=msg, default=d)
    if not safe:
        print prompt
        x = sys.stdin.readline().strip()
    else:
        x = getpass.getpass(prompt=prompt)
    if x == '' and default is not None:
        return default
    return x

server = 'https://www.edx.org'
course_id = 'HarvardX/PH207x/2012_Fall'
location = 'i4x://HarvardX/PH207x/problem/ex_practice_2'

#server = prompt('Server (no trailing slash)',  'http://127.0.0.1:8000')
#course_id = prompt('Course id', 'edX/7012x/2013_Spring')
#location = prompt('problem location', 'i4x://edX/7012x/problem/example_upload_answer')
value = prompt('value to upload')

username = prompt('username on server', 'victor@edx.org')
password = prompt('password', 'abc123', safe=True)

print "get csrf cookie"
session = requests.Session()
r = session.get(server + '/')
r.raise_for_status()

# print session.cookies

# for some reason, the server expects a header containing the csrf cookie, not just the
# cookie itself.
session.headers['X-CSRFToken'] = session.cookies['csrftoken']
# for https, need a referer header
session.headers['Referer'] = server + '/'
login_url = '/'.join([server, 'login'])

print "log in"
r = session.post(login_url, {'email': 'victor@edx.org', 'password': 'Secret!', 'remember': 'false'})
#print "request headers: ", r.request.headers
#print "response headers: ", r.headers
r.raise_for_status()

url = '/'.join([server, 'courses', course_id, 'modx', location, 'problem_check'])
data = {'input_{0}_2_1'.format(location.replace('/','-').replace(':','').replace('--','-')): value}
#data = {'input_i4x-edX-7012x-problem-example_upload_answer_2_1': value}

print "Posting to '{0}': {1}".format(url, data)

r = session.post(url, data)
r.raise_for_status()

print ("To see the uploaded answer, go to {server}/courses/{course_id}/jump_to/{location}"
       .format(server=server, course_id=course_id, location=location))
