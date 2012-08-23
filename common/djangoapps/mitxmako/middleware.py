#   Copyright (c) 2008 Mikeal Rogers
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distribuetd under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from mako.lookup import TemplateLookup
import tempfile
from django.template import RequestContext
from django.conf import settings

requestcontext = None
lookup = {}


class MakoMiddleware(object):
    def __init__(self):
        """Setup mako variables and lookup object"""
        # Set all mako variables based on django settings
        template_locations = settings.MAKO_TEMPLATES
        module_directory = getattr(settings, 'MAKO_MODULE_DIR', None)

        if module_directory is None:
            module_directory = tempfile.mkdtemp()

        for location in template_locations:
            lookup[location] = TemplateLookup(directories=template_locations[location],
                                module_directory=module_directory,
                                output_encoding='utf-8',
                                input_encoding='utf-8',
                                encoding_errors='replace',
                                )

        import mitxmako
        mitxmako.lookup = lookup

    def process_request(self, request):
        global requestcontext
        requestcontext = RequestContext(request)
        requestcontext['is_secure'] = request.is_secure()
        requestcontext['site'] = request.get_host()
