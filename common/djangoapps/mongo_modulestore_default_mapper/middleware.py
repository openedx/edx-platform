"""
This middleware will inspect the incoming request and allow for mapping of a hostname
to a particular modulestore class
"""
import threading
import logging
from django.conf import settings

import xmodule.modulestore.django

_request_default_modulestore_mapping_local = threading.local()
_request_default_modulestore_mapping_local.default_modulestore = 'default'

# IMPORTANT:
# Monkey patch the function to return the default modulestore name
# this is how to hook into the modulestore factory
xmodule.modulestore.django.get_default_modulestore_name = lambda: _request_default_modulestore_mapping_local.default_modulestore
    
class DefaultModulestoreMapper(object):

    def reset_default_modulestore(self):
        """
        Clears out the thread local
        """
        global _request_default_modulestore_mapping_local
        _request_default_modulestore_mapping_local.default_modulestore = 'default'

    def process_request(self, request):
        """
        Middleware HTTP request entry point for beginning of request
        """
        global _request_default_modulestore_mapping_local

        self.reset_default_modulestore()
        mappings = getattr(settings, 'MONGO_DEFAULT_CONFIG_MAPPINGS', None)

        domain = request.META.get('HTTP_HOST')
        domain = domain.split(':')[0]
        if domain and mappings:
            if domain in mappings:
                _request_default_modulestore_mapping_local.default_modulestore = mappings[domain]

        return None

    def process_response(self, request, response):
        """
        Middleware HTTP request entry point for end of request
        """
        self.reset_default_modulestore()
        return response