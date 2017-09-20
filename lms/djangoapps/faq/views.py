import json
import re

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from edxmako.shortcuts import render_to_response, render_to_string

from lms.djangoapps.faq.models import Faq


@login_required
def get_faq(request):
    """
    Display the Dynamic FAQ Page
    """

    faq_page = Faq.objects.filter(is_active=True).last()
    if not faq_page:
        return HttpResponseNotFound(render_to_string('static_templates/404.html', {}, request=request))

    body = re.search('<body>(.*)</body>', faq_page.content, re.S)

    context = {
        'title': faq_page.title,
        'body': mark_safe(body.group(1)) if body else 'No Content',
    }
    return render_to_response("faq/custom_faq.html", context)


@csrf_exempt
def get_faq_title(request):
    """
    Get the the Dynamic FAQ Page Title
    """

    # Default Title is FAQ
    data = {'page_title': 'FAQ'}

    if request.is_ajax():
        faq_page = Faq.objects.filter(is_active=True).last()

        if faq_page:
            data = json.dumps({"page_title": faq_page.title})

    return JsonResponse(data)
