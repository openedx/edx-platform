"""
Views that are only activated when the project is running in development mode.
These views will NOT be shown on production: trying to access them will result
in a 404 error.
"""
from mako.exceptions import TopLevelLookupException
from django.http import HttpResponseNotFound

from openedx.core.djangoapps.edxmako.shortcuts import render_to_response


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
        context = {
            "disable_courseware_js": True,
            "uses_pattern_library": True
        }
        context.update(request.GET.dict())
        return render_to_response(template, context)
    except TopLevelLookupException:
        return HttpResponseNotFound("Couldn't find template {template}".format(template=template))
