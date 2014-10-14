import logging

from xmodule.modulestore.django import modulestore
from student.roles import CourseInstructorRole
from student.models import UserProfile

from courseware.courses import get_course_about_section
from .edraakcertificate import EdraakCertificate
from opaque_keys.edx import locator

logger = logging.getLogger(__name__)


def generate_certificate(request, course_id):
    user = request.user
    course_key = locator.CourseLocator.from_string(course_id)
    course = modulestore().get_course(course_key)

    course_name = course.display_name
    course_end_date = ''
    if course.end:
        course_end_date = str(course.end.date())
    course_short_desc = get_course_about_section(course, 'short_description')

    instructor_name = ''
    role = CourseInstructorRole(course_key)
    if role.users_with_role():
        instructor_user = role.users_with_role()[0]
        instructor_name = UserProfile.objects.get(user=instructor_user).name

    cert = EdraakCertificate(course_name=course_name,
                             user_profile_name=user.profile.name,
                             course_org=course.display_organization,
                             course_end_date=course_end_date,
                             course_desc=course_short_desc,
                             instructor=instructor_name)

    cert.generate_and_save()

    return cert.temp_file