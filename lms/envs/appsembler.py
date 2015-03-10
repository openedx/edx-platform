import os

from path import path

from .common import *

#### from aws.py 
SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)
CONFIG_ROOT = path(os.environ.get('CONFIG_ROOT', ENV_ROOT))
CONFIG_PREFIX = SERVICE_VARIANT + "." if SERVICE_VARIANT else ""
with open(CONFIG_ROOT / CONFIG_PREFIX + "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

#### begin Appsembler specific changes
# GOOGLE_TAG_MANAGER_ID = os.environ.get("GOOGLE_TAG_MANAGER_ID", None)
GOOGLE_TAG_MANAGER_ID = ENV_TOKENS.get('GOOGLE_TAG_MANAGER_ID', os.environ.get("GOOGLE_TAG_MANAGER_ID", None))

# intercom.Intercom.app_id = ENV_TOKENS.get('INTERCOM_APP_ID', os.environ.get("INTERCOM_APP_ID", ""))
# intercom.Intercom.api_key = ENV_TOKENS.get('INTERCOM_API_KEY', os.environ.get("INTERCOM_API_KEY", ""))
INTERCOM_APP_ID = ENV_TOKENS.get('INTERCOM_APP_ID', os.environ.get("INTERCOM_APP_ID", ""))
INTERCOM_API_KEY = ENV_TOKENS.get('INTERCOM_API_KEY', os.environ.get("INTERCOM_API_KEY", ""))
INTERCOM_USER_EMAIL = ENV_TOKENS.get('INTERCOM_USER_EMAIL', os.environ.get("INTERCOM_USER_EMAIL", ""))
