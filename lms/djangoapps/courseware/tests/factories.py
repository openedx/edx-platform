from datetime import datetime
import json
from functools import partial

from factory import DjangoModelFactory, SubFactory
from student.tests.factories import UserFactory as StudentUserFactory
from student.tests.factories import GroupFactory as StudentGroupFactory
from student.tests.factories import UserProfileFactory as StudentUserProfileFactory
from student.tests.factories import CourseEnrollmentAllowedFactory as StudentCourseEnrollmentAllowedFactory
from student.tests.factories import RegistrationFactory as StudentRegistrationFactory

from courseware.models import StudentModule, XModuleUserStateSummaryField
from courseware.models import XModuleStudentInfoField, XModuleStudentPrefsField, OfflineComputedGrade

from xmodule.modulestore import Location
from pytz import UTC

location = partial(Location, 'i4x', 'edX', 'test_course', 'problem')


class UserProfileFactory(StudentUserProfileFactory):
    name = 'Robot Studio'
    courseware = 'course.xml'


class RegistrationFactory(StudentRegistrationFactory):
    pass


class UserFactory(StudentUserFactory):
    email = 'robot@edx.org'
    last_name = 'Tester'
    last_login = datetime.now(UTC)
    date_joined = datetime.now(UTC)


class GroupFactory(StudentGroupFactory):
    name = 'test_group'


class CourseEnrollmentAllowedFactory(StudentCourseEnrollmentAllowedFactory):
    pass


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


class OfflineComputedGradeFactory(DjangoModelFactory):
    FACTORY_FOR = OfflineComputedGrade

    user = SubFactory(UserFactory)
    course_id = "MITx/999/Robot_Super_Course"
    gradeset = json.dumps({})
