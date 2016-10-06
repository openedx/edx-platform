"""
Mako template subclass that can render as if it is a Django template.
"""

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

from django.conf import settings
from mako.template import Template as MakoTemplate

import openedx.core.djangoapps.edxmako
from openedx.core.djangoapps.edxmako.request_context import get_template_request_context
from openedx.core.djangoapps.edxmako.shortcuts import marketing_link

# TODO: We should make this a Django Template subclass that simply has
# the MakoTemplate inside of it? (instead of inheriting from MakoTemplate)


class Template(MakoTemplate):
    """
    This bridges the gap between a Mako template and a Django template. It can
    be rendered like it is a django template because the arguments are transformed
    in a way that MakoTemplate can understand.
    """

    def __init__(self, *args, **kwargs):
        """Overrides base __init__ to provide django variable overrides"""
        if not kwargs.get('no_django', False):
            kwargs['lookup'] = openedx.core.djangoapps.edxmako.LOOKUP['main']
        super(Template, self).__init__(*args, **kwargs)

    def render(self, context_instance):  # pylint: disable=arguments-differ
        """
        This takes a render call with a context (from Django) and translates
        it to a render call on the mako template.
        """
        # collapse context_instance to a single dictionary for mako
        context_dictionary = {}

        # In various testing contexts, there might not be a current request context.
        request_context = get_template_request_context()
        if request_context:
            for item in request_context:
                context_dictionary.update(item)
        for item in context_instance:
            context_dictionary.update(item)
        context_dictionary['settings'] = settings
        context_dictionary['EDX_ROOT_URL'] = settings.EDX_ROOT_URL
        context_dictionary['django_context'] = context_instance
        context_dictionary['marketing_link'] = marketing_link

        return super(Template, self).render_unicode(**context_dictionary)
