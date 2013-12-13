import urllib2
import uuid

CLIENT_ID = "77zv1vf44fo92m"
CLIENT_SECRET = "1M3wZUNA2aYHldbv"
REDIRECT_URI = "http://www.edx.org"
STATE = uuid.uuid4()
SCOPE = "%20".join([
    "r_basicprofile",
    "r_fullprofile",
    "r_emailaddress",
    "r_network",
    "r_contactinfo",
    "rw_nus",
    "rw_company_admin",
    "rw_groups",
    "w_messages"])

print "Go here:"
print ("https://www.linkedin.com/uas/oauth2/authorization?response_type=code"
       "&client_id=%s&state=%s&redirect_uri=%s&scope=%s" %
       (CLIENT_ID, STATE, REDIRECT_URI, SCOPE))

print "Enter authcode: ",
code = raw_input()

url = ("https://www.linkedin.com/uas/oauth2/accessToken"
       "?grant_type=authorization_code"
       "&code=%s&redirect_uri=%s&client_id=%s&client_secret=%s" % (
           code, REDIRECT_URI, CLIENT_ID, CLIENT_SECRET))
try:
    print urllib2.urlopen(url).read()
except urllib2.HTTPError, e:
    print "!!ERROR!!"
    print e
    print e.read()
