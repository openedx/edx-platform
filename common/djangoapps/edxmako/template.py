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
from edxmako.shortcuts import marketing_link

import edxmako
import edxmako.middleware

DJANGO_VARIABLES = ['output_encoding', 'encoding_errors']

# TODO: We should make this a Django Template subclass that simply has the MakoTemplate inside of it? (Intead of inheriting from MakoTemplate)


class Template(MakoTemplate):
    """
    This bridges the gap between a Mako template and a djano template. It can
    be rendered like it is a django template because the arguments are transformed
    in a way that MakoTemplate can understand.
    """

    def __init__(self, *args, **kwargs):
        """Overrides base __init__ to provide django variable overrides"""
        if not kwargs.get('no_django', False):
            overrides = {k: getattr(edxmako, k, None) for k in DJANGO_VARIABLES}
            overrides['lookup'] = edxmako.LOOKUP['main']
            kwargs.update(overrides)
        super(Template, self).__init__(*args, **kwargs)

    def render(self, context_instance):
        """
        This takes a render call with a context (from Django) and translates
        it to a render call on the mako template.
        """
        # collapse context_instance to a single dictionary for mako
        context_dictionary = {}

        # In various testing contexts, there might not be a current request context.
        if getattr(edxmako.middleware.REQUEST_CONTEXT, "context", None):
            for d in edxmako.middleware.REQUEST_CONTEXT.context:
                context_dictionary.update(d)
        for d in context_instance:
            context_dictionary.update(d)
        context_dictionary['settings'] = settings
        context_dictionary['EDX_ROOT_URL'] = settings.EDX_ROOT_URL
        context_dictionary['django_context'] = context_instance
        context_dictionary['marketing_link'] = marketing_link

        return super(Template, self).render_unicode(**context_dictionary)
