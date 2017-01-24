"""A openid store using django cache"""

from openid.store.interface import OpenIDStore
from openid.store import nonce

from django.core.cache import cache

import logging
import time

DEFAULT_ASSOCIATIONS_TIMEOUT = 60
DEFAULT_NONCE_TIMEOUT = 600

ASSOCIATIONS_KEY_PREFIX = 'openid.provider.associations.'
NONCE_KEY_PREFIX = 'openid.provider.nonce.'

log = logging.getLogger('DjangoOpenIDStore')


def get_url_key(server_url):
    """
    Returns the URL key for the given server_url.
    """
    return ASSOCIATIONS_KEY_PREFIX + server_url


def get_nonce_key(server_url, timestamp, salt):
    """
    Returns the nonce for the given parameters.
    """
    return '{prefix}{url}.{ts}.{salt}'.format(
        prefix=NONCE_KEY_PREFIX,
        url=server_url,
        ts=timestamp,
        salt=salt,
    )


class DjangoOpenIDStore(OpenIDStore):
    """
    django implementation of OpenIDStore.
    """
    def __init__(self):
        log.info('DjangoStore cache:' + str(cache.__class__))

    def storeAssociation(self, server_url, assoc):
        key = get_url_key(server_url)

        log.info('storeAssociation {0}'.format(key))

        associations = cache.get(key, {})
        associations[assoc.handle] = assoc

        cache.set(key, associations, DEFAULT_ASSOCIATIONS_TIMEOUT)

    def getAssociation(self, server_url, handle=None):
        key = get_url_key(server_url)

        log.info('getAssociation {0}'.format(key))

        associations = cache.get(key, {})

        assoc = None

        if handle is None:
            # get best association
            valid_assocs = [a for a in associations if a.getExpiresIn() > 0]
            if valid_assocs:
                valid_assocs.sort(lambda a: a.getExpiresIn(), reverse=True)
                assoc = valid_assocs.sort[0]
        else:
            assoc = associations.get(handle)

        # check expiration and remove if it has expired
        if assoc and assoc.getExpiresIn() <= 0:
            if handle is None:
                cache.delete(key)
            else:
                associations.pop(handle)
                cache.set(key, associations, DEFAULT_ASSOCIATIONS_TIMEOUT)
            assoc = None

        return assoc

    def removeAssociation(self, server_url, handle):
        key = get_url_key(server_url)

        log.info('removeAssociation {0}'.format(key))

        associations = cache.get(key, {})

        removed = False

        if associations:
            if handle is None:
                cache.delete(key)
                removed = True
            else:
                assoc = associations.pop(handle, None)
                if assoc:
                    cache.set(key, associations, DEFAULT_ASSOCIATIONS_TIMEOUT)
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
