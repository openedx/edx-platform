from django.http import HttpResponseNotFound
from edxmako.shortcuts import render_to_string


def render_404(request):
    return HttpResponseNotFound(render_to_string('custom_templates/404.html', {}, request=request))