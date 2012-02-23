from aws import *

# Staging specific overrides
SITE_NAME = "staging.mitx.mit.edu"
AWS_STORAGE_BUCKET_NAME = 'mitx_askbot_stage'
CACHES['default']['LOCATION'] = ['***REMOVED***', 
			                     '***REMOVED***']

### Secure Data Below Here ###
SECRET_KEY = ""
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""

