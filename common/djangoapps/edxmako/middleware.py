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

import ConfigParser
from django.conf import settings
from django.template import RequestContext
from util.request import safe_get_host
requestcontext = None


class MakoMiddleware(object):

    def process_request(self, request):
        global requestcontext
        requestcontext = RequestContext(request)
        requestcontext['is_secure'] = request.is_secure()
        requestcontext['site'] = safe_get_host(request)
        requestcontext['doc_url'] = self.get_doc_url_func(request)

    def get_doc_url_func(self, request):
        config_file = open(settings.REPO_ROOT / "docs" / "config.ini")
        config = ConfigParser.ConfigParser()
        config.readfp(config_file)

        # in the future, we will detect the locale; for now, we will
        # hardcode en_us, since we only have English documentation
        locale = "en_us"

        def doc_url(token):
            try:
                return config.get(locale, token)
            except ConfigParser.NoOptionError:
                return config.get(locale, "default")

        return doc_url
