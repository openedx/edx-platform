# Factories are self documenting


import json
from functools import partial

import factory
from django.test.client import RequestFactory
from factory.django import DjangoModelFactory
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import CourseLocator

from lms.djangoapps.courseware.models import (
    StudentModule,
    XModuleStudentInfoField,
    XModuleStudentPrefsField,
    XModuleUserStateSummaryField
)
from common.djangoapps.student.roles import (
    CourseBetaTesterRole,
    CourseInstructorRole,
    CourseStaffRole,
    GlobalStaff,
    OrgInstructorRole,
    OrgStaffRole
)
# Imported to re-export
from common.djangoapps.student.tests.factories import UserFactory  # Imported to re-export
from common.djangoapps.student.tests.factories import UserProfileFactory as StudentUserProfileFactory

# TODO fix this (course_id and location are invalid names as constants, and course_id should really be COURSE_KEY)
# pylint: disable=invalid-name
course_id = CourseKey.from_string('edX/test_course/test')
location = partial(course_id.make_usage_key, u'problem')


class UserProfileFactory(StudentUserProfileFactory):
    courseware = 'course.xml'


# For the following factories, these are disabled because we're ok ignoring the
# unused arguments create and **kwargs in the line:
# course_key(self, create, extracted, **kwargs)
# pylint: disable=unused-argument

class InstructorFactory(UserFactory):
    """
    Given a course Location, returns a User object with instructor
    permissions for `course`.
    """
    last_name = "Instructor"

    @factory.post_generation
    def course_key(self, create, extracted, **kwargs):
        if extracted is None:
            raise ValueError("Must specify a CourseKey for a course instructor user")
        CourseInstructorRole(extracted).add_users(self)


class StaffFactory(UserFactory):
    """
    Given a course Location, returns a User object with staff
    permissions for `course`.
    """
    last_name = "Staff"

    @factory.post_generation
    def course_key(self, create, extracted, **kwargs):
        if extracted is None:
            raise ValueError("Must specify a CourseKey for a course staff user")
        CourseStaffRole(extracted).add_users(self)


class BetaTesterFactory(UserFactory):
    """
    Given a course Location, returns a User object with beta-tester
    permissions for `course`.
    """
    last_name = "Beta-Tester"

    @factory.post_generation
    def course_key(self, create, extracted, **kwargs):
        if extracted is None:
            raise ValueError("Must specify a CourseKey for a beta-tester user")
        CourseBetaTesterRole(extracted).add_users(self)


class OrgStaffFactory(UserFactory):
    """
    Given a course Location, returns a User object with org-staff
    permissions for `course`.
    """
    last_name = "Org-Staff"

    @factory.post_generation
    def course_key(self, create, extracted, **kwargs):
        if extracted is None:
            raise ValueError("Must specify a CourseKey for an org-staff user")
        OrgStaffRole(extracted.org).add_users(self)


class OrgInstructorFactory(UserFactory):
    """
    Given a course Location, returns a User object with org-instructor
    permissions for `course`.
    """
    last_name = "Org-Instructor"

    @factory.post_generation
    def course_key(self, create, extracted, **kwargs):
        if extracted is None:
            raise ValueError("Must specify a CourseKey for an org-instructor user")
        OrgInstructorRole(extracted.org).add_users(self)


class GlobalStaffFactory(UserFactory):
    """
    Returns a User object with global staff access
    """
    last_name = "GlobalStaff"

    @factory.post_generation
    def set_staff(self, create, extracted, **kwargs):
        GlobalStaff().add_users(self)
# pylint: enable=unused-argument


class StudentModuleFactory(DjangoModelFactory):
    class Meta(object):
        model = StudentModule

    module_type = "problem"
    student = factory.SubFactory(UserFactory)
    course_id = CourseLocator("MITx", "999", "Robot_Super_Course")
    state = None
    grade = None
    max_grade = None
    done = 'na'


class UserStateSummaryFactory(DjangoModelFactory):
    class Meta(object):
        model = XModuleUserStateSummaryField

    field_name = 'existing_field'
    value = json.dumps('old_value')
    usage_id = location('usage_id')


class StudentPrefsFactory(DjangoModelFactory):
    class Meta(object):
        model = XModuleStudentPrefsField

    field_name = 'existing_field'
    value = json.dumps('old_value')
    student = factory.SubFactory(UserFactory)
    module_type = 'mock_problem'


class StudentInfoFactory(DjangoModelFactory):
    class Meta(object):
        model = XModuleStudentInfoField

    field_name = 'existing_field'
    value = json.dumps('old_value')
    student = factory.SubFactory(UserFactory)


class RequestFactoryNoCsrf(RequestFactory):
    """
    RequestFactory, which disables csrf checks.
    """
    def request(self, **kwargs):
        request = super(RequestFactoryNoCsrf, self).request(**kwargs)
        setattr(request, '_dont_enforce_csrf_checks', True)  # pylint: disable=literal-used-as-attribute
        return request
