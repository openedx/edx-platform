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

import logging

log = logging.getLogger("mitx." + __name__)

from django.template import Context
from django.http import HttpResponse

from . import middleware
from django.conf import settings


def render_to_string(template_name, dictionary, context=None, namespace='main'):
    context_instance = Context(dictionary)
    # add dictionary to context_instance
    context_instance.update(dictionary or {})
    # collapse context_instance to a single dictionary for mako
    context_dictionary = {}
    context_instance['settings'] = settings
    context_instance['MITX_ROOT_URL'] = settings.MITX_ROOT_URL

    # In various testing contexts, there might not be a current request context.
    if middleware.requestcontext is not None:
        for d in middleware.requestcontext:
            context_dictionary.update(d)
    for d in context_instance:
        context_dictionary.update(d)
    if context:
        context_dictionary.update(context)
    # fetch and render template
    template = middleware.lookup[namespace].get_template(template_name)
    return template.render(**context_dictionary)


def render_to_response(template_name, dictionary, context_instance=None, namespace='main', **kwargs):
    """
    Returns a HttpResponse whose content is filled with the result of calling
    lookup.get_template(args[0]).render with the passed arguments.
    """
    return HttpResponse(render_to_string(template_name, dictionary, context_instance, namespace), **kwargs)
