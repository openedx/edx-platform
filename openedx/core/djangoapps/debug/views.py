"""
Views that are only activated when the project is running in development mode.
These views will NOT be shown on production: trying to access them will result
in a 404 error.
"""
from django.http import HttpResponseNotFound
from django.utils.translation import ugettext as _
from edxmako.shortcuts import render_to_response
from mako.exceptions import TopLevelLookupException
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
        uses_bootstrap = u'/bootstrap/' in request.path
        uses_pattern_library = u'/pattern-library/' in request.path
        is_v1 = u'/v1/' in request.path
        context = {
            "disable_courseware_js": not is_v1,
            "uses_pattern_library": uses_pattern_library,
            "uses_bootstrap": uses_bootstrap,
        }
        context.update(request.GET.dict())

        # Add some messages to the course skeleton pages
        if u'course-skeleton.html' in request.path:
            PageLevelMessages.register_info_message(request, _('This is a test message'))
            PageLevelMessages.register_success_message(request, _('This is a success message'))
            PageLevelMessages.register_warning_message(request, _('This is a test warning'))
            PageLevelMessages.register_error_message(request, _('This is a test error'))

        return render_to_response(template, context)
    except TopLevelLookupException:
        return HttpResponseNotFound("Couldn't find template {template}".format(template=template))
