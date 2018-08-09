import json
import logging

import django.utils
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.http import HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from opaque_keys.edx.keys import CourseKey

from cms.djangoapps.contentstore.views.course import get_course_and_check_access
from edxmako.shortcuts import render_to_response
from util.json_request import JsonResponse, expect_json
from util.views import require_global_staff
from xmodule.modulestore.django import modulestore
from .models import CustomSettings

log = logging.getLogger(__name__)


@require_global_staff
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT"))
@expect_json
def course_custom_settings(request, course_key_string):
    """
    Course custom settings configuration
    GET
        html: get the page
    PUT, POST
        json: update the Course's custom settings.
    """

    course_key = CourseKey.from_string(course_key_string)

    with modulestore().bulk_operations(course_key):
        course_module = get_course_and_check_access(course_key, request.user)
        try:
            settings = CustomSettings.objects.get(id=course_key)
        except ObjectDoesNotExist as exc:
            return HttpResponseBadRequest(django.utils.html.escape(exc.message), content_type="text/plain")

        if 'text/html' in request.META.get('HTTP_ACCEPT', '') and request.method == 'GET':
            return render_to_response('custom_settings.html', {
                'context_course': course_module,
                'custom_dict': {'is_featured': settings.is_featured, 'show_grades': settings.show_grades,
                                'tags': settings.tags},
                'custom_settings_url': reverse('custom_settings', kwargs={'course_key_string': unicode(course_key)}),
            })

        elif 'application/json' in request.META.get('HTTP_ACCEPT', '') and request.method in ['POST', 'PUT']:
            body = json.loads(request.body)
            settings.is_featured = body.get('is_featured') if isinstance(body.get('is_featured'), bool) else False
            settings.show_grades = body.get('show_grades') if isinstance(body.get('show_grades'), bool) else False
            settings.tags = body.get('tags')
            settings.save()
            return JsonResponse(body)

        else:
            return HttpResponseNotAllowed("Bad Request", content_type="text/plain")
