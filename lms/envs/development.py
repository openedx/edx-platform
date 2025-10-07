"""
This settings file is optimized for local development.  It should work equally well for bare-metal development and for
running inside of development environments such as tutor.
"""

#Helpers for loading plugins and their settings.
from edx_django_utils.plugins import add_plugins
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType

# Use the common file as the starting point.
from .common import *
from openedx.core.lib.derived import Derived, derive_settings

DEBUG = True

STORAGES['default']['BACKEND'] = 'django.core.files.storage.FileSystemStorage'
STORAGES['staticfiles']['BACKEND'] = 'openedx.core.storage.DevelopmentStorage'

# Disable pipeline compression in development
PIPELINE['PIPELINE_ENABLED'] = False

# Revert to the default set of finders as we don't want the production pipeline
STATICFILES_FINDERS = [
    'openedx.core.djangoapps.theming.finders.ThemeFilesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.PipelineFinder',
]

# Whether to run django-require in debug mode.
REQUIRE_DEBUG = DEBUG

LMS_BASE = 'local.openedx.io:18000'
LMS_ROOT_URL = f'http://{LMS_BASE}'
ALLOWED_HOSTS = ['local.openedx.io']

# Add JWTs so we can get reliable session keys
# TODO: It would be nice to link to how we generate these secrets.
JWT_AUTH.update({
    'JWT_PRIVATE_SIGNING_JWK': """
        {
            "kid": "devstack_key",
            "kty": "RSA",
            "key_ops": [
                "sign"
            ],
            "n": "smKFSYowG6nNUAdeqH1jQQnH1PmIHphzBmwJ5vRf1vu48BUI5VcVtUWIPqzRK_LDSlZYh9D0YFL0ZTxIrlb6Tn3Xz7pYvpIAeYuQv3_H5p8tbz7Fb8r63c1828wXPITVTv8f7oxx5W3lFFgpFAyYMmROC4Ee9qG5T38LFe8_oAuFCEntimWxN9F3P-FJQy43TL7wG54WodgiM0EgzkeLr5K6cDnyckWjTuZbWI-4ffcTgTZsL_Kq1owa_J2ngEfxMCObnzGy5ZLcTUomo4rZLjghVpq6KZxfS6I1Vz79ZsMVUWEdXOYePCKKsrQG20ogQEkmTf9FT_SouC6jPcHLXw",
            "e": "AQAB",
            "d": "RQ6k4NpRU3RB2lhwCbQ452W86bMMQiPsa7EJiFJUg-qBJthN0FMNQVbArtrCQ0xA1BdnQHThFiUnHcXfsTZUwmwvTuiqEGR_MI6aI7h5D8vRj_5x-pxOz-0MCB8TY8dcuK9FkljmgtYvV9flVzCk_uUb3ZJIBVyIW8En7n7nV7JXpS9zey1yVLld2AbRG6W5--Pgqr9JCI5-bLdc2otCLuen2sKyuUDHO5NIj30qGTaKUL-OW_PgVmxrwKwccF3w5uGNEvMQ-IcicosCOvzBwdIm1uhdm9rnHU1-fXz8VLRHNhGVv7z6moghjNI0_u4smhUkEsYeshPv7RQEWTdkOQ",
            "p": "7KWj7l-ZkfCElyfvwsl7kiosvi-ppOO7Imsv90cribf88DexcO67xdMPesjM9Nh5X209IT-TzbsOtVTXSQyEsy42NY72WETnd1_nAGLAmfxGdo8VV4ZDnRsA8N8POnWjRDwYlVBUEEeuT_MtMWzwIKU94bzkWVnHCY5vbhBYLeM",
            "q": "wPkfnjavNV1Hqb5Qqj2crBS9HQS6GDQIZ7WF9hlBb2ofDNe2K2dunddFqCOdvLXr7ydRcK51ZwSeHjcjgD1aJkHA9i1zqyboxgd0uAbxVDo6ohnlVqYLtap2tXXcavKm4C9MTpob_rk6FBfEuq4uSsuxFvCER4yG3CYBBa4gZVU",
            "dp": "MO9Ppss-Bl-mC1vGyJDBbMgr2GgivGYbHFLt6ERfTGsvcr0RhDjZu16ZpNpBB6B7-K-uJGHxPmmf8P9KRWDBUAwOSaT2a-pTsuux6PKCwVTZfUq5LxAkiyg6WZTGoWASEtoae0XRHEy2TvIKNl5AiX-h_DwDPDbEYcWCZVAb6-E",
            "dq": "m03j7GkGSWRxMGNCeEBtvvBR4vDS9Her7AtjbNSWnRxDMQrKSdRMaiu-m7tOT3n6D9cM7Cr7wZUtzBOENskprHBu47FgzfXakMWfYhv0TV0voxZERKAN_H7cWt4oLsprEzH9r6THsxFPdKxMYBGeoAOe2l9nlk26m6LaX7_rwqE",
            "qi": "jnJ0nfARyAcHsezENNrXKnDM-LrMJWMHPh_70ZM_pF5iRMOLojHkTVsUIzYi6Uj2ohX9Jz1zsV207kCuPqQXURbhlt1xEaktwCmySeWU4qkMTptWp4ya2jEwGn8EKJ1iEc0GhDkRyLrgm4ol-sq9DMaKEkhTGy4Y3-8mMCBVqeQ"
        }
""",
    'JWT_PUBLIC_SIGNING_JWK_SET': (
        '{"keys": [{"kid": "devstack_key", "e": "AQAB", "kty": "RSA", "n": "smKFSYowG6nNUAdeqH1jQQnH1PmIHphzBmwJ5vRf1vu'
        '48BUI5VcVtUWIPqzRK_LDSlZYh9D0YFL0ZTxIrlb6Tn3Xz7pYvpIAeYuQv3_H5p8tbz7Fb8r63c1828wXPITVTv8f7oxx5W3lFFgpFAyYMmROC'
        '4Ee9qG5T38LFe8_oAuFCEntimWxN9F3P-FJQy43TL7wG54WodgiM0EgzkeLr5K6cDnyckWjTuZbWI-4ffcTgTZsL_Kq1owa_J2ngEfxMCObnzG'
        'y5ZLcTUomo4rZLjghVpq6KZxfS6I1Vz79ZsMVUWEdXOYePCKKsrQG20ogQEkmTf9FT_SouC6jPcHLXw"}]}'
    ),
})

#######################################################################################################################
#### DERIVE ANY DERIVED SETTINGS
####

derive_settings(__name__)
add_plugins(__name__, ProjectType.LMS, SettingsType.DEVSTACK)
