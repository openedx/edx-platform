import requests
from urllib import quote_plus
from pprint import pprint

def get_cs50_grades(email):
    """

    """
    base_url = 'http://apps.cs50.edx.org/'
    slug = '5075680a-88a0-4562-8e41-7fe30a000204'

    s = requests.session()

    r = s.post(base_url + 'users/authenticate', data={'slug': slug})

    if r.json is None or not r.json['User']:
        # auth failed
        print "auth failed.  Response:" + r.text
    else:
        print "auth response: " + str(r.json)

    # # What is a suite id?
    suite_id = 7
    r = s.get(base_url + str(suite_id))

    print 'response to suite selection: ' + r.text[:200]

    #user_token = quote_plus(r.json['User']['token'])
    user_token = quote_plus(email)
    grades = s.get(base_url + "gradebook/grades/user/{0}".format(user_token))
    #grades = s.get(base_url + "gradebook/grades/") #/user/{0}".format(user_token))
    print 'grades: '
    pprint(grades.json)
