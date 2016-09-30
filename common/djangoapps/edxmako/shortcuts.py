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

from django.template import Context
from django.http import HttpResponse
import logging

from microsite_configuration import microsite

from edxmako import lookup_template
from edxmako.middleware import get_template_request_context
from django.conf import settings
from django.core.urlresolvers import reverse
log = logging.getLogger(__name__)


def marketing_link(name):
    """Returns the correct URL for a link to the marketing site
    depending on if the marketing site is enabled

    Since the marketing site is enabled by a setting, we have two
    possible URLs for certain links. This function is to decides
    which URL should be provided.
    """

    # link_map maps URLs from the marketing site to the old equivalent on
    # the Django site
    link_map = settings.MKTG_URL_LINK_MAP
    enable_mktg_site = microsite.get_value(
        'ENABLE_MKTG_SITE',
        settings.FEATURES.get('ENABLE_MKTG_SITE', False)
    )

    if enable_mktg_site and name in settings.MKTG_URLS:
        # special case for when we only want the root marketing URL
        if name == 'ROOT':
            return settings.MKTG_URLS.get('ROOT')
        return settings.MKTG_URLS.get('ROOT') + settings.MKTG_URLS.get(name)
    # only link to the old pages when the marketing site isn't on
    elif not enable_mktg_site and name in link_map:
        # don't try to reverse disabled marketing links
        if link_map[name] is not None:
            return reverse(link_map[name])
    else:
        log.debug("Cannot find corresponding link for name: %s", name)
        return '#'


def is_any_marketing_link_set(names):
    """
    Returns a boolean if any given named marketing links are configured.
    """

    return any(is_marketing_link_set(name) for name in names)


def is_marketing_link_set(name):
    """
    Returns a boolean if a given named marketing link is configured.
    """

    enable_mktg_site = microsite.get_value(
        'ENABLE_MKTG_SITE',
        settings.FEATURES.get('ENABLE_MKTG_SITE', False)
    )

    if enable_mktg_site:
        return name in settings.MKTG_URLS
    else:
        return name in settings.MKTG_URL_LINK_MAP


def marketing_link_context_processor(request):
    """
    A django context processor to give templates access to marketing URLs

    Returns a dict whose keys are the marketing link names usable with the
    marketing_link method (e.g. 'ROOT', 'CONTACT', etc.) prefixed with
    'MKTG_URL_' and whose values are the corresponding URLs as computed by the
    marketing_link method.
    """
    return dict(
        [
            ("MKTG_URL_" + k, marketing_link(k))
            for k in (
                settings.MKTG_URL_LINK_MAP.viewkeys() |
                settings.MKTG_URLS.viewkeys()
            )
        ]
    )


def open_source_footer_context_processor(request):
    """
    Checks the site name to determine whether to use the edX.org footer or the Open Source Footer.
    """
    return dict(
        [
            ("IS_EDX_DOMAIN", settings.FEATURES.get('IS_EDX_DOMAIN', False))
        ]
    )


def using_custom_theme_context_processor(request):
    """
    Checks using custom theme in templates
    """
    return dict(
        [
            ("USE_CUSTOM_THEME", settings.FEATURES.get('USE_CUSTOM_THEME', False))
        ]
    )


def microsite_footer_context_processor(request):
    """
    Checks the site name to determine whether to use the edX.org footer or the Open Source Footer.
    """
    return dict(
        [
            ("IS_REQUEST_IN_MICROSITE", microsite.is_request_in_microsite())
        ]
    )


def render_to_string(template_name, dictionary, context=None, namespace='main'):

    # see if there is an override template defined in the microsite
    template_name = microsite.get_template_path(template_name)

    context_instance = Context(dictionary)
    # add dictionary to context_instance
    context_instance.update(dictionary or {})
    # collapse context_instance to a single dictionary for mako
    context_dictionary = {}
    context_instance['settings'] = settings
    context_instance['EDX_ROOT_URL'] = settings.EDX_ROOT_URL
    context_instance['marketing_link'] = marketing_link
    context_instance['is_any_marketing_link_set'] = is_any_marketing_link_set
    context_instance['is_marketing_link_set'] = is_marketing_link_set

    # In various testing contexts, there might not be a current request context.
    request_context = get_template_request_context()
    if request_context:
        for item in request_context:
            context_dictionary.update(item)
    for item in context_instance:
        context_dictionary.update(item)
    if context:
        context_dictionary.update(context)

    # "Fix" CSRF token by evaluating the lazy object
    KEY_CSRF_TOKENS = ('csrf_token', 'csrf')
    for key in KEY_CSRF_TOKENS:
        if key in context_dictionary:
            context_dictionary[key] = unicode(context_dictionary[key])

    # fetch and render template
    template = lookup_template(namespace, template_name)
    return template.render_unicode(**context_dictionary)


def render_to_response(template_name, dictionary=None, context_instance=None, namespace='main', **kwargs):
    """
    Returns a HttpResponse whose content is filled with the result of calling
    lookup.get_template(args[0]).render with the passed arguments.
    """

    # see if there is an override template defined in the microsite
    template_name = microsite.get_template_path(template_name)

    dictionary = dictionary or {}
    return HttpResponse(render_to_string(template_name, dictionary, context_instance, namespace), **kwargs)
