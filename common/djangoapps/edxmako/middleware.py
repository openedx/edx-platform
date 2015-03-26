#   Copyright (c) 2008 Mikeal Rogers
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import threading
from django.template import RequestContext
from util.request import safe_get_host

REQUEST_CONTEXT = threading.local()


class MakoMiddleware(object):

    def process_request(self, request):
        """ Process the middleware request. """
        REQUEST_CONTEXT.request = request

    def process_response(self, __, response):
        """ Process the middleware response. """
        REQUEST_CONTEXT.request = None
        return response


def get_template_request_context():
    """
    Returns the template processing context to use for the current request,
    or returns None if there is not a current request.
    """
    request = getattr(REQUEST_CONTEXT, "request", None)
    if not request:
        return None
    context = RequestContext(request)
    context['is_secure'] = request.is_secure()
    context['site'] = safe_get_host(request)
    return context
