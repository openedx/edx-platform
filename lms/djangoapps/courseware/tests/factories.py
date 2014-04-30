import json
from functools import partial
import factory
from factory.django import DjangoModelFactory

# Imported to re-export
# pylint: disable=unused-import
from student.tests.factories import UserFactory  # Imported to re-export
# pylint: enable=unused-import

from student.tests.factories import UserProfileFactory as StudentUserProfileFactory
from courseware.models import StudentModule, XModuleUserStateSummaryField
from courseware.models import XModuleStudentInfoField, XModuleStudentPrefsField
from student.roles import (
    CourseInstructorRole,
    CourseStaffRole,
    CourseBetaTesterRole,
    GlobalStaff,
    OrgStaffRole,
    OrgInstructorRole,
)

from xmodule.modulestore.locations import SlashSeparatedCourseKey


course_id = SlashSeparatedCourseKey(u'edX', u'test_course', u'test')
location = partial(course_id.make_usage_key, u'problem')


class UserProfileFactory(StudentUserProfileFactory):
    courseware = 'course.xml'


class InstructorFactory(UserFactory):
    """
    Given a course Location, returns a User object with instructor
    permissions for `course`.
    """
    last_name = "Instructor"

    @factory.post_generation
    # TODO Change this from course to course_key at next opportunity
    def course(self, create, extracted, **kwargs):
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
    # TODO Change this from course to course_key at next opportunity
    def course(self, create, extracted, **kwargs):
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
    # TODO Change this from course to course_key at next opportunity
    def course(self, create, extracted, **kwargs):
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
    # TODO Change this from course to course_key at next opportunity
    def course(self, create, extracted, **kwargs):
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
    # TODO Change this from course to course_key at next opportunity
    def course(self, create, extracted, **kwargs):
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


class StudentModuleFactory(DjangoModelFactory):
    FACTORY_FOR = StudentModule

    module_type = "problem"
    student = factory.SubFactory(UserFactory)
    course_id = SlashSeparatedCourseKey("MITx", "999", "Robot_Super_Course")
    state = None
    grade = None
    max_grade = None
    done = 'na'


class UserStateSummaryFactory(DjangoModelFactory):
    FACTORY_FOR = XModuleUserStateSummaryField

    field_name = 'existing_field'
    value = json.dumps('old_value')
    usage_id = location('usage_id')


class StudentPrefsFactory(DjangoModelFactory):
    FACTORY_FOR = XModuleStudentPrefsField

    field_name = 'existing_field'
    value = json.dumps('old_value')
    student = factory.SubFactory(UserFactory)
    module_type = 'mock_problem'


class StudentInfoFactory(DjangoModelFactory):
    FACTORY_FOR = XModuleStudentInfoField

    field_name = 'existing_field'
    value = json.dumps('old_value')
    student = factory.SubFactory(UserFactory)
