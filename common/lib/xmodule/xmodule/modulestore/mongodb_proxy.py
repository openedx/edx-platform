"""
https://github.com/arngarden/MongoDBProxy

Copyright 2013 Gustav Arngarden

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

from functools import wraps
import logging
import pymongo
import time

log = logging.getLogger(__name__)

MONGO_METHODS_NEEDING_RETRY = {
    pymongo.collection.Collection: [
        'aggregate', 'ensure_index', 'find', 'group', 'inline_map_reduce', 'map_reduce', 'parallel_scan'
    ],
}


def autoretry_read(wait=0.1, tries=5):
    """
    Automatically retry a read-only method in the case of a pymongo
    AutoReconnect exception.

    See http://emptysqua.re/blog/save-the-monkey-reliably-writing-to-mongodb/
    for a discussion of this technique.
    """
    def decorate(func):  # pylint: disable=missing-docstring
        @wraps(func)
        def wrapper(*args, **kwargs):  # pylint: disable=missing-docstring
            for attempt in xrange(tries):
                try:
                    return func(*args, **kwargs)
                except pymongo.errors.AutoReconnect:
                    log.exception('Attempt {0}'.format(attempt))
                    # Reraise if we failed on our last attempt
                    if attempt == tries - 1:
                        raise

                    if wait:
                        time.sleep(wait)
        return wrapper
    return decorate


class MongoProxy:
    """
    Proxy for MongoDB connection.
    Methods that are executable, i.e find, insert etc, get wrapped in an
    Executable-instance that handles AutoReconnect-exceptions transparently.
    """
    def __init__(self, proxied_object, wait_time=None, methods_needing_retry=None):
        """
        proxied_object is an ordinary MongoDB-connection.
        """
        self.proxied_object = proxied_object
        self.wait_time = wait_time
        self.methods_needing_retry = methods_needing_retry or MONGO_METHODS_NEEDING_RETRY

    def __getitem__(self, key):
        """
        Create and return proxy around attribute "key" if it is a method.
        Otherwise just return the attribute.
        """
        item = self.proxied_object[key]
        if hasattr(item, '__call__'):
            return MongoProxy(item, self.wait_time)
        return item

    def __setitem__(self, key, value):
        self.proxied_object[key] = value

    def __delitem__(self, key):
        del self.proxied_object[key]

    def __len__(self):
        return len(self.proxied_object)

    def __getattr__(self, key):
        """
        If key is the name of an executable method in the MongoDB connection,
        for instance find or insert, wrap this method in Executable-class that
        handles AutoReconnect-Exception.
        """
        attr = getattr(self.proxied_object, key)
        if hasattr(attr, '__call__'):
            attributes_for_class = self.methods_needing_retry.get(self.proxied_object.__class__, [])
            if key in attributes_for_class:
                return autoretry_read(self.wait_time)(attr)
            else:
                return MongoProxy(attr, self.wait_time)
        return attr

    def __call__(self, *args, **kwargs):
        return self.proxied_object(*args, **kwargs)

    def __dir__(self):
        return dir(self.proxied_object)

    def __str__(self):
        return self.proxied_object.__str__()

    def __repr__(self):
        return self.proxied_object.__repr__()

    def __nonzero__(self):
        return True
