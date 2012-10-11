"""
Settings for the LMS that runs alongside the CMS on AWS
"""

from ..aws import *

with open(ENV_ROOT / "cms.auth.json") as auth_file:
    CMS_AUTH_TOKENS = json.load(auth_file)

MODULESTORE = CMS_AUTH_TOKENS['MODULESTORE']
