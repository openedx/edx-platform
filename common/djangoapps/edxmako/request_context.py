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
#
# This file has been modified by edX.org

"""
Methods for creating RequestContext for using with Mako templates.
"""


from crum import get_current_request
from django.template import RequestContext

from edx_django_utils.cache import RequestCache
from openedx.core.lib.request_utils import safe_get_host


def get_template_request_context(request=None):
    """
    Returns the template processing context to use for the current request,
    or returns None if there is not a current request.
    """

    if request is None:
        request = get_current_request()

    if request is None:
        return None

    request_cache_dict = RequestCache('edxmako').data
    cache_key = "request_context"
    if cache_key in request_cache_dict:
        return request_cache_dict[cache_key]

    context = RequestContext(request)

    context['is_secure'] = request.is_secure()
    context['site'] = safe_get_host(request)

    request_cache_dict[cache_key] = context

    return context
