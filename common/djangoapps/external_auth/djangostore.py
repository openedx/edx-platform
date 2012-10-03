"""A openid store using django cache"""

from openid.store.interface import OpenIDStore
from openid.store import nonce

from django.core.cache import cache

import logging
import time

DEFAULT_ASSOCIATION_TIMEOUT = 60
DEFAULT_NONCE_TIMEOUT = 600

ASSOCIATIONS_KEY_PREFIX = 'openid.provider.associations.'
NONCE_KEY_PREFIX = 'openid.provider.nonce.'

log = logging.getLogger('DjangoOpenIDStore')


def get_url_key(server_url):
    key = ASSOCIATIONS_KEY_PREFIX + server_url
    return key


def get_nonce_key(server_url, timestamp, salt):
    key = '{prefix}{url}.{ts}.{salt}'.format(prefix=NONCE_KEY_PREFIX,
                                             url=server_url,
                                             ts=timestamp,
                                             salt=salt)
    return key


class DjangoOpenIDStore(OpenIDStore):
    def __init__(self):
        log.info('DjangoStore cache:' + str(cache.__class__))

    def storeAssociation(self, server_url, association):
        key = get_url_key(server_url)

        log.info('storeAssociation {0}'.format(key))

        associations = cache.get(key, {})
        associations[association.handle] = association

        cache.set(key, associations, DEFAULT_ASSOCIATION_TIMEOUT)

    def getAssociation(self, server_url, handle=None):
        key = get_url_key(server_url)

        log.info('getAssociation {0}'.format(key))

        associations = cache.get(key)

        association = None

        if associations:
            if handle is None:
                # get best association
                valid = [a for a in associations if a.getExpiresIn() > 0]
                if valid:
                    association = valid[0]
            else:
                association = associations.get(handle)

        # check expiration and remove if it has expired
        if association and association.getExpiresIn() <= 0:
            if handle is None:
                cache.delete(key)
            else:
                associations.pop(handle)
                cache.set(key, association, DEFAULT_ASSOCIATION_TIMEOUT)
            association = None

        return association

    def removeAssociation(self, server_url, handle):
        key = get_url_key(server_url)

        log.info('removeAssociation {0}'.format(key))

        associations = cache.get(key)

        removed = False

        if associations:
            if handle is None:
                cache.delete(key)
                removed = True
            else:
                association = associations.pop(handle)
                if association:
                    cache.set(key, association, DEFAULT_ASSOCIATION_TIMEOUT)
                    removed = True

        return removed

    def useNonce(self, server_url, timestamp, salt):
        key = get_nonce_key(server_url, timestamp, salt)

        log.info('useNonce {0}'.format(key))

        if abs(timestamp - time.time()) > nonce.SKEW:
            return False

        anonce = cache.get(key)

        found = False

        if anonce is None:
            cache.set(key, '-', DEFAULT_NONCE_TIMEOUT)
            found = False
        else:
            found = True

        return found

    def cleanupNonces(self):
        # not necesary, keys will timeout
        return 0

    def cleanupAssociations(self):
        # not necesary, keys will timeout
        return 0
