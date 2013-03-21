from student.models import (User, UserProfile, Registration,
                            CourseEnrollmentAllowed, CourseEnrollment)
from django.contrib.auth.models import Group
from datetime import datetime
from factory import Factory, SubFactory
from uuid import uuid4


class GroupFactory(Factory):
    FACTORY_FOR = Group

    name = 'staff_MITx/999/Robot_Super_Course'


class UserProfileFactory(Factory):
    FACTORY_FOR = UserProfile

    user = None
    name = 'Robot Test'
    level_of_education = None
    gender = 'm'
    mailing_address = None
    goals = 'World domination'


class RegistrationFactory(Factory):
    FACTORY_FOR = Registration

    user = None
    activation_key = uuid4().hex


class UserFactory(Factory):
    FACTORY_FOR = User

    username = 'robot'
    email = 'robot+test@edx.org'
    password = 'test'
    first_name = 'Robot'
    last_name = 'Test'
    is_staff = False
    is_active = True
    is_superuser = False
    last_login = datetime(2012, 1, 1)
    date_joined = datetime(2011, 1, 1)


class CourseEnrollmentFactory(Factory):
    FACTORY_FOR = CourseEnrollment

    user = SubFactory(UserFactory)
    course_id = 'edX/toy/2012_Fall'


class CourseEnrollmentAllowedFactory(Factory):
    FACTORY_FOR = CourseEnrollmentAllowed

    email = 'test@edx.org'
    course_id = 'edX/test/2012_Fall'
