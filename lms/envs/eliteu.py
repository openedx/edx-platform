"""
eliteu envs
"""

import logging
import json
import os
from path import Path as path
from .common import ENV_ROOT, FEATURES, INSTALLED_APPS, MIDDLEWARE_CLASSES

log = logging.getLogger(__name__)


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

ENV_FEATURES = ENV_TOKENS.get('FEATURES', {})
for feature, value in ENV_FEATURES.items():
    FEATURES[feature] = value

# Apple In-app purchase
APPLE_VERIFY_RECEIPT_IS_SANDBOX = ENV_TOKENS.get('APPLE_VERIFY_RECEIPT_IS_SANDBOX', '')
APPLE_VERIFY_RECEIPT_URL = ENV_TOKENS.get('APPLE_VERIFY_RECEIPT_URL', '')
APPLE_VERIFY_RECEIPT_SANDBOX_URL = ENV_TOKENS.get('APPLE_VERIFY_RECEIPT_SANDBOX_URL', '')
APPLE_IN_APP_PRODUCT_ID = AUTH_TOKENS.get('APPLE_IN_APP_PRODUCT_ID', {})

# verify student
SHOW_VERIFY_STUDENT_SUPPORT = FEATURES.get('SHOW_VERIFY_STUDENT_SUPPORT', True)

# Sentry
try:
    SENTRY_DSN_FRONTEND = ENV_FEATURES.get('SENTRY_DSN_FRONTEND', '')
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    sentry_dsn_backend = ENV_FEATURES.get('SENTRY_DSN_BACKEND', '')
    if sentry_dsn_backend:
        sentry_sdk.init(
            dsn=sentry_dsn_backend,
            integrations=[DjangoIntegration()]
        )
        log.info("Sentry Start Up Success")
except ImportError:
    log.info("Sentry Module Import Error")

# CourseSearch
SEARCH_SORT = ENV_TOKENS.get('SEARCH_SORT', None)

# App Version
MOBILE_APP_USER_AGENT_REGEXES = ENV_TOKENS.get('MOBILE_APP_USER_AGENT_REGEXES', None)

# Baidu Bridge
BAIDU_BRIDGE_URL = ENV_TOKENS.get('BAIDU_BRIDGE_URL', '')

# Ministry of industry URL and  the record number
ELITE_CASE_NUMBER = ENV_TOKENS.get('ELITE_CASE_NUMBER', "")
ELITE_FILING_WEBSITE = ENV_TOKENS.get('ELITE_FILING_WEBSITE', "")

# elitemba
import imp
HMM_ENABLED = ENV_FEATURES.get('HMM_ENABLED', False)
try:
    if HMM_ENABLED:
        fp, elitemba_path, desc = imp.find_module('elitemba')
        INSTALLED_APPS.append('elitemba')
        MIDDLEWARE_CLASSES.append('elitemba.middleware.ElitembaDataMiddleware')
        HMM_CONFIGS = ENV_FEATURES.get('HMM_CONFIGS', {
            'HOST': 'https://openapi.myhbp.org.cn',
            'APP_ID': '',
            'SOURCE_ID': '',
            'LHOST': 'https://myhbp.org.cn',
        })
except ImportError:
    HMM_ENABLED = False
    print "Warnning: missing package 'elitemba'"

