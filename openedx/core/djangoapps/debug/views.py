"""
Views that are only activated when the project is running in development mode.
These views will NOT be shown on production: trying to access them will result
in a 404 error.
"""


import bleach
from django.http import HttpResponseNotFound
from django.template import TemplateDoesNotExist
from django.utils.translation import ugettext as _

from common.djangoapps.edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.util.user_messages import PageLevelMessages


def show_reference_template(request, template):
    """
    Shows the specified template as an HTML page. This is used only in
    debug mode to allow the UX team to produce and work with static
    reference templates.

    e.g. http://localhost:8000/template/ux/reference/index.html
    shows the template from ux/reference/index.html

    Note: dynamic parameters can also be passed to the page.
    e.g. /template/ux/reference/index.html?name=Foo
    """
    try:
        is_v1 = u'/v1/' in request.path
        uses_bootstrap = not is_v1
        context = {
            'request': request,
            'uses_bootstrap': uses_bootstrap,
        }
        context.update(request.GET.dict())

        # Support dynamic rendering of messages
        if request.GET.get('alert'):
            PageLevelMessages.register_info_message(request, request.GET.get('alert'))
        if request.GET.get('success'):
            PageLevelMessages.register_success_message(request, request.GET.get('success'))
        if request.GET.get('warning'):
            PageLevelMessages.register_warning_message(request, request.GET.get('warning'))
        if request.GET.get('error'):
            PageLevelMessages.register_error_message(request, request.GET.get('error'))

        # Add some messages to the course skeleton pages
        if u'course-skeleton.html' in request.path:
            PageLevelMessages.register_info_message(request, _('This is a test message'))
            PageLevelMessages.register_success_message(request, _('This is a success message'))
            PageLevelMessages.register_warning_message(request, _('This is a test warning'))
            PageLevelMessages.register_error_message(request, _('This is a test error'))

        return render_to_response(template, context)
    except TemplateDoesNotExist:
        return HttpResponseNotFound(u'Missing template {template}'.format(template=bleach.clean(template, strip=True)))
