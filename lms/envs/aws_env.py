"""
A Django settings file that overrides a subset
of the configuration from the environment
"""

from .aws import *
import os


# Mysql overrides

DB_OVERRIDES = dict(
    PASSWORD=os.environ.get('EDXAPP_MYSQL_PASSWORD', None),
    USER=os.environ.get('EDXAPP_MYSQL_USER', None),
    NAME=os.environ.get('EDXAPP_MYSQL_DB_NAME', None),
    HOST=os.environ.get('EDXAPP_MYSQL_HOST', None),
    PORT=os.environ.get('EDXAPP_MYSQL_PORT', None),
)

# Mongo overrides

MONGO_OVERRIDES = dict(
    password=os.environ.get('EDXAPP_MONGO_PASSWORD', None),
    user=os.environ.get('EDXAPP_MONGO_USER', None),
    db=os.environ.get('EDXAPP_MONGO_DB_NAME', None),
    port=os.environ.get('EDXAPP_MONGO_PORT', None),

)

if os.environ.get('EDXAPP_MONGO_HOSTS', None):
    MONGO_OVERRIDES['host'] = os.environ.get('EDXAPP_MONGO_HOSTS').split(',')
if MONGO_OVERRIDES['port']:
    MONGO_OVERRIDES['port'] = int(MONGO_OVERRIDES['port'])
# Memcache overrides

MEMCACHE_OVERRIDES = dict()

if os.environ.get('EDXAPP_MEMCACHE_HOSTS', None):
    MEMCACHE_OVERRIDES['LOCATION'] = os.environ.get('EDXAPP_MEMCACHE_HOSTS').split(',')

# Update the settings with the overrides

for override, value in DB_OVERRIDES.iteritems():
    if value:
        DATABASES['default'][override] = value

for override, value in MONGO_OVERRIDES.iteritems():
    if value:
        CONTENTSTORE['DOC_STORE_CONFIG'][override] = value
        CONTENTSTORE['OPTIONS'][override] = value
        DOC_STORE_CONFIG[override] = value
        MODULESTORE['default']['OPTIONS']['stores']['default']['DOC_STORE_CONFIG'][override] = value
        MODULESTORE['default']['OPTIONS']['stores']['default']['OPTIONS'][override] = value
        MODULESTORE['draft']['DOC_STORE_CONFIG'][override] = value
        MODULESTORE['draft']['OPTIONS'][override] = value

for override, value in MEMCACHE_OVERRIDES.iteritems():
    if value:
        for cache in CACHES.keys():
            if override in CACHES[cache]:
                CACHES[cache][override] = value
