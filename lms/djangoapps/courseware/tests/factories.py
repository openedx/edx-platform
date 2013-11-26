import json
from functools import partial

from factory import DjangoModelFactory, SubFactory, post_generation

# Imported to re-export
# pylint: disable=unused-import
from student.tests.factories import UserFactory  # Imported to re-export
from student.tests.factories import GroupFactory  # Imported to re-export
from student.tests.factories import CourseEnrollmentAllowedFactory  # Imported to re-export
from student.tests.factories import RegistrationFactory  # Imported to re-export
# pylint: enable=unused-import

from student.tests.factories import UserProfileFactory as StudentUserProfileFactory
from courseware.models import StudentModule, XModuleUserStateSummaryField
from courseware.models import XModuleStudentInfoField, XModuleStudentPrefsField
from courseware.roles import CourseInstructorRole, CourseStaffRole

from xmodule.modulestore import Location


location = partial(Location, 'i4x', 'edX', 'test_course', 'problem')


class UserProfileFactory(StudentUserProfileFactory):
    courseware = 'course.xml'


class InstructorFactory(UserFactory):
    """
    Given a course Location, returns a User object with instructor
    permissions for `course`.
    """
    last_name = "Instructor"

    @post_generation
    def course(self, create, extracted, **kwargs):
        if extracted is None:
            raise ValueError("Must specify a course location for a course instructor user")
        CourseInstructorRole(extracted).add_users(self)


class StaffFactory(UserFactory):
    """
    Given a course Location, returns a User object with staff
    permissions for `course`.
    """
    last_name = "Staff"

    @post_generation
    def course(self, create, extracted, **kwargs):
        if extracted is None:
            raise ValueError("Must specify a course location for a course staff user")
        CourseStaffRole(extracted).add_users(self)


class StudentModuleFactory(DjangoModelFactory):
    FACTORY_FOR = StudentModule

    module_type = "problem"
    student = SubFactory(UserFactory)
    course_id = "MITx/999/Robot_Super_Course"
    state = None
    grade = None
    max_grade = None
    done = 'na'


class UserStateSummaryFactory(DjangoModelFactory):
    FACTORY_FOR = XModuleUserStateSummaryField

    field_name = 'existing_field'
    value = json.dumps('old_value')
    usage_id = location('def_id').url()


class StudentPrefsFactory(DjangoModelFactory):
    FACTORY_FOR = XModuleStudentPrefsField

    field_name = 'existing_field'
    value = json.dumps('old_value')
    student = SubFactory(UserFactory)
    module_type = 'MockProblemModule'


class StudentInfoFactory(DjangoModelFactory):
    FACTORY_FOR = XModuleStudentInfoField

    field_name = 'existing_field'
    value = json.dumps('old_value')
    student = SubFactory(UserFactory)
