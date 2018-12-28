"""
eliteu envs
"""

import logging
import json
import os
from path import Path as path
from .common import ENV_ROOT, FEATURES

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

