"""
Views that are only activated when the project is running in development mode.
These views will NOT be shown on production: trying to access them will result
in a 404 error.
"""
# pylint: disable=unused-argument
from edxmako.shortcuts import render_to_response
from mako.exceptions import TopLevelLookupException
from django.http import HttpResponseNotFound


def dev_mode(request):
    "Sample static view"
    return render_to_response("dev/dev_mode.html")


def dev_show_template(request, template):
    """
    Shows the specified template as an HTML page.
    e.g. /template/ux/reference/container.html shows the template under ux/reference/container.html

    Note: dynamic parameters can also be passed to the page.
    e.g. /template/ux/reference/container.html?name=Foo
    """
    try:
        return render_to_response(template, request.GET.dict())
    except TopLevelLookupException:
        return HttpResponseNotFound("Couldn't find template {tpl}".format(tpl=template))
