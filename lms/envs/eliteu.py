"""
eliteu envs
"""

import json
import os
from path import Path as path
from .common import ENV_ROOT


# SERVICE_VARIANT specifies name of the variant used, which decides what JSON
# configuration files are read during startup.
SERVICE_VARIANT = os.environ.get('SERVICE_VARIANT', None)

# CONFIG_ROOT specifies the directory where the JSON configuration
# files are expected to be found. If not specified, use the project
# directory.
CONFIG_ROOT = path(os.environ.get('CONFIG_ROOT', ENV_ROOT))

# CONFIG_PREFIX specifies the prefix of the JSON configuration files,
# based on the service variant. If no variant is use, don't use a
# prefix.
CONFIG_PREFIX = SERVICE_VARIANT + "." if SERVICE_VARIANT else ""


with open(CONFIG_ROOT / CONFIG_PREFIX + "env.json") as env_file:
    ENV_TOKENS = json.load(env_file)

with open(CONFIG_ROOT / CONFIG_PREFIX + "auth.json") as auth_file:
    AUTH_TOKENS = json.load(auth_file)

# Apple In-app purchase
APPLE_VERIFY_RECEIPT_IS_SANDBOX = ENV_TOKENS.get('APPLE_VERIFY_RECEIPT_URL', '')
APPLE_VERIFY_RECEIPT_URL = ENV_TOKENS.get('APPLE_VERIFY_RECEIPT_URL', '')
APPLE_VERIFY_RECEIPT_SANDBOX_URL = ENV_TOKENS.get('APPLE_VERIFY_RECEIPT_SANDBOX_URL', '')
APPLE_IN_APP_PRODUCT_ID = AUTH_TOKENS.get('APPLE_IN_APP_PRODUCT_ID', {})
