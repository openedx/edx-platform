# A simple script demonstrating how to have an external program save results to the server

import requests
import sys

def prompt(msg, default=None):
    d = ' [{0}]'.format(default) if default is not None else ''
    print 'Enter {msg}{default}: '.format(msg=msg, default=d)
    x = sys.stdin.readline().strip()
    if x == '' and default is not None:
        return default
    return x

#     http://127.0.0.1:8000/courses/MITx/7012x/2013_Spring/modx/i4x://MITx/7012x/problem/example_functional_groups/problem_check


server = prompt('Server (no trailing slash)',  'http://127.0.0.1:8000')
course_id = prompt('Course id', 'MITx/7012x/2013_Spring')
location = prompt('problem location', 'i4x://MITx/7012x/problem/example_upload_answer')
value = prompt('value to upload')

print "logging in"
session = requests.session()
r = session.get(server + '/')
r.raise_for_status()
print session.cookies

# for some reason, the server expects a header containing the csrf cookie, not just the
# cookie itself.
session.headers['X-CSRFToken'] = session.cookies['csrftoken']
login_url = '/'.join([server, 'login'])

r = session.post(login_url, {'email': 'victor@edx.org', 'password': 'abc123'})
print "request headers: ", r.request.headers
print "response headers: ", r.headers
r.raise_for_status()

url = '/'.join([server, 'courses', course_id, 'modx', location, 'problem_check'])
data = {'input_{0}_2_1'.format(location.replace('/','-').replace(':','').replace('--','-')): value}
#data = {'input_i4x-MITx-7012x-problem-example_upload_answer_2_1': value}



print "Posting to '{0}': {1}".format(url, data)

r = session.post(url, data)
r.raise_for_status()
