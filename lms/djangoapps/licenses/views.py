import logging
from collections import namedtuple, defaultdict

from mitxmako.shortcuts import render_to_string

from models import get_courses_licenses, get_or_create_license


log = logging.getLogger("mitx.licenses")


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
