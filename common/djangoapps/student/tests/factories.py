"""Provides factories for student models."""


from datetime import datetime
from uuid import uuid4

import factory
import six
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.contenttypes.models import ContentType
from factory.django import DjangoModelFactory
from opaque_keys.edx.keys import CourseKey
from pytz import UTC

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from common.djangoapps.student.models import (
    AccountRecovery,
    CourseAccessRole,
    CourseEnrollment,
    CourseEnrollmentAllowed,
    CourseEnrollmentCelebration,
    PendingEmailChange,
    Registration,
    User,
    UserProfile,
    UserStanding
)

# Factories are self documenting

TEST_PASSWORD = 'test'


class GroupFactory(DjangoModelFactory):
    class Meta(object):
        model = Group
        django_get_or_create = ('name', )

    name = factory.Sequence(u'group{0}'.format)


class UserStandingFactory(DjangoModelFactory):
    class Meta(object):
        model = UserStanding

    user = None
    account_status = None
    changed_by = None


class UserProfileFactory(DjangoModelFactory):
    class Meta(object):
        model = UserProfile
        django_get_or_create = ('user', )

    user = None
    name = factory.LazyAttribute(u'{0.user.first_name} {0.user.last_name}'.format)
    level_of_education = None
    gender = u'm'
    mailing_address = None
    goals = u'Learn a lot'
    allow_certificate = True


class RegistrationFactory(DjangoModelFactory):
    class Meta(object):
        model = Registration

    user = None
    activation_key = six.text_type(uuid4().hex)


class UserFactory(DjangoModelFactory):
    class Meta(object):
        model = User
        django_get_or_create = ('email', 'username')

    _DEFAULT_PASSWORD = 'test'

    username = factory.Sequence(u'robot{0}'.format)
    email = factory.Sequence(u'robot+test+{0}@edx.org'.format)
    password = factory.PostGenerationMethodCall('set_password', _DEFAULT_PASSWORD)
    first_name = factory.Sequence(u'Robot{0}'.format)
    last_name = 'Test'
    is_staff = False
    is_active = True
    is_superuser = False
    last_login = datetime(2012, 1, 1, tzinfo=UTC)
    date_joined = datetime(2011, 1, 1, tzinfo=UTC)

    @factory.post_generation
    def profile(obj, create, extracted, **kwargs):  # pylint: disable=unused-argument, missing-function-docstring
        if create:
            obj.save()
            return UserProfileFactory.create(user=obj, **kwargs)
        elif kwargs:
            raise Exception("Cannot build a user profile without saving the user")
        else:
            return None

    @factory.post_generation
    def groups(self, create, extracted, **kwargs):
        if extracted is None:
            return

        if isinstance(extracted, six.string_types):
            extracted = [extracted]

        for group_name in extracted:
            self.groups.add(GroupFactory.simple_generate(create, name=group_name))


class AnonymousUserFactory(factory.Factory):
    class Meta(object):
        model = AnonymousUser


class AdminFactory(UserFactory):
    is_staff = True


class SuperuserFactory(UserFactory):
    is_superuser = True


class CourseEnrollmentFactory(DjangoModelFactory):
    class Meta(object):
        model = CourseEnrollment

    user = factory.SubFactory(UserFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        manager = cls._get_manager(model_class)
        course_kwargs = {}
        for key in list(kwargs):
            if key.startswith('course__'):
                course_kwargs[key.split('__')[1]] = kwargs.pop(key)

        if 'course' not in kwargs:
            course_id = kwargs.get('course_id')
            course_overview = None
            if course_id is not None:
                # 'course_id' is not needed by the model when course is passed.
                # This arg used to be called course_id before we added the CourseOverview
                # foreign key constraint to CourseEnrollment.
                del kwargs['course_id']

                if isinstance(course_id, six.string_types):
                    course_id = CourseKey.from_string(course_id)
                    course_kwargs.setdefault('id', course_id)

                try:
                    course_overview = CourseOverview.get_from_id(course_id)
                except CourseOverview.DoesNotExist:
                    pass

            if course_overview is None:
                if 'id' not in course_kwargs and course_id:
                    course_kwargs['id'] = course_id

                course_overview = CourseOverviewFactory(**course_kwargs)
            kwargs['course'] = course_overview

        return manager.create(*args, **kwargs)


class CourseEnrollmentCelebrationFactory(DjangoModelFactory):
    class Meta:
        model = CourseEnrollmentCelebration

    enrollment = factory.SubFactory(CourseEnrollmentFactory)


class CourseAccessRoleFactory(DjangoModelFactory):
    class Meta(object):
        model = CourseAccessRole

    user = factory.SubFactory(UserFactory)
    course_id = CourseKey.from_string('edX/toy/2012_Fall')
    role = 'TestRole'


class CourseEnrollmentAllowedFactory(DjangoModelFactory):
    class Meta(object):
        model = CourseEnrollmentAllowed

    email = 'test@edx.org'
    course_id = CourseKey.from_string('edX/toy/2012_Fall')


class PendingEmailChangeFactory(DjangoModelFactory):
    """Factory for PendingEmailChange objects

    user: generated by UserFactory
    new_email: sequence of new+email+{}@edx.org
    activation_key: sequence of integers, padded to 30 characters
    """
    class Meta(object):
        model = PendingEmailChange

    user = factory.SubFactory(UserFactory)
    new_email = factory.Sequence(u'new+email+{0}@edx.org'.format)
    activation_key = factory.Sequence(u'{:0<30d}'.format)


class ContentTypeFactory(DjangoModelFactory):
    class Meta(object):
        model = ContentType

    app_label = factory.Faker('app_name')


class PermissionFactory(DjangoModelFactory):
    class Meta(object):
        model = Permission

    codename = factory.Faker('codename')
    content_type = factory.SubFactory(ContentTypeFactory)


class AccountRecoveryFactory(DjangoModelFactory):
    class Meta(object):
        model = AccountRecovery
        django_get_or_create = ('user',)

    user = None
    secondary_email = factory.Sequence(u'robot+test+recovery+{0}@edx.org'.format)
    is_active = True
