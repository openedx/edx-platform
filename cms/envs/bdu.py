"""
Set of custom values user for Big Data University deployments
"""

from .aws import *

#### BDU config files ##########################################################
with open(CONFIG_ROOT / "bdu.env.json") as env_file:
    BDU_ENV_TOKENS = json.load(env_file)

with open(CONFIG_ROOT / "bdu.auth.json") as env_file:
    BDU_AUTH_TOKENS = json.load(env_file)

### BDU Labs ##################################################################
BDU_LABS_ROOT_URL = BDU_ENV_TOKENS.get('BDU_LABS_ROOT_URL')

# BDU Labs API
BDU_LABS_API_URL = BDU_ENV_TOKENS.get('BDU_LABS_API_URL')
BDU_LABS_ACCESS_KEY = BDU_AUTH_TOKENS.get('BDU_LABS_ACCESS_KEY')
BDU_LABS_SECRET_KEY = BDU_AUTH_TOKENS.get('BDU_LABS_SECRET_KEY')
