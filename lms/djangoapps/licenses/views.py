import logging
import json
import re
from urlparse import urlparse
from collections import namedtuple, defaultdict


from edxmako.shortcuts import render_to_string
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import requires_csrf_token

from licenses.models import CourseSoftware
from licenses.models import get_courses_licenses, get_or_create_license, get_license


log = logging.getLogger("edx.licenses")


License = namedtuple('License', 'software serial')


def get_licenses_by_course(user, courses):
    licenses = get_courses_licenses(user, courses)
    licenses_by_course = defaultdict(list)

    # create missing licenses and group by course_id
    for software, license in licenses.iteritems():
        if license is None:
            licenses[software] = get_or_create_license(user, software)

        course_id = software.course_id
        serial = license.serial if license else None
        licenses_by_course[course_id].append(License(software, serial))

    # render elements
    data_by_course = {}
    for course_id, licenses in licenses_by_course.iteritems():
        context = {'licenses': licenses}
        template = 'licenses/serial_numbers.html'
        data_by_course[course_id] = render_to_string(template, context)

    return data_by_course


@login_required
@requires_csrf_token
def user_software_license(request):
    if request.method != 'POST' or not request.is_ajax():
        raise Http404

    # get the course id from the referer
    url_path = urlparse(request.META.get('HTTP_REFERER', '')).path
    pattern = re.compile('^/courses/(?P<id>[^/]+/[^/]+/[^/]+)/.*/?$')
    match = re.match(pattern, url_path)

    if not match:
        raise Http404
    course_id = match.groupdict().get('id', '')
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)

    user_id = request.session.get('_auth_user_id')
    software_name = request.POST.get('software')
    generate = request.POST.get('generate', False) == 'true'

    try:
        software = CourseSoftware.objects.get(name=software_name,
                                              course_id=course_key)
    except CourseSoftware.DoesNotExist:
        raise Http404

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        raise Http404

    if generate:
        software_license = get_or_create_license(user, software)
    else:
        software_license = get_license(user, software)

    if software_license:
        response = {'serial': software_license.serial}
    else:
        response = {'error': 'No serial number found'}

    return HttpResponse(json.dumps(response), mimetype='application/json')
