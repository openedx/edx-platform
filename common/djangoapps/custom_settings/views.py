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

from .helpers import get_course_open_date_from_settings, validate_course_open_date
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
                'course_short_id': settings.course_short_id if settings else "N/A",
                'custom_dict': {
                    'enable_enrollment_email': settings.enable_enrollment_email,
                    'is_featured': settings.is_featured,
                    'show_grades': settings.show_grades,
                    'tags': settings.tags,
                    'seo_tags': "" if not settings.seo_tags else json.loads(settings.seo_tags),
                    'course_open_date': get_course_open_date_from_settings(settings),
                    'auto_enroll': settings.auto_enroll,
                    'is_mini_lesson': settings.is_mini_lesson
                },
                'custom_settings_url': reverse('custom_settings', kwargs={'course_key_string': unicode(course_key)}),
            })

        elif 'application/json' in request.META.get('HTTP_ACCEPT', '') and request.method in ['POST', 'PUT']:
            body = json.loads(request.body)
            course_open_date = validate_course_open_date(settings, body.get('course_open_date'))
            settings.is_featured = body.get('is_featured') if isinstance(body.get('is_featured'), bool) else False
            settings.show_grades = body.get('show_grades') if isinstance(body.get('show_grades'), bool) else False
            settings.course_open_date = course_open_date
            settings.tags = body.get('tags')
            settings.seo_tags = None if body.get('seo_tags') == "" else json.dumps(body.get('seo_tags'))
            settings.enable_enrollment_email = body.get('enable_enrollment_email')
            settings.auto_enroll = body.get('auto_enroll')
            settings.is_mini_lesson = body.get('is_mini_lesson')
            settings.save()
            return JsonResponse(body)

        else:
            return HttpResponseNotAllowed("Bad Request", content_type="text/plain")
