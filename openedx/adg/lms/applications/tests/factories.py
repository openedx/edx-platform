"""
All model factories for applications
"""
import factory

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.applications.models import (
    ApplicationHub,
    BusinessLine,
    Education,
    MultilingualCourse,
    MultilingualCourseGroup,
    Reference,
    UserApplication,
    WorkExperience
)
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory


class BusinessLineFactory(factory.DjangoModelFactory):
    """
    Factory for BusinessLine model
    """

    class Meta:
        model = BusinessLine

    title = factory.Faker('word')
    description = factory.Faker('sentence')


class UserApplicationFactory(factory.DjangoModelFactory):
    """
    Factory for UserApplication model
    """

    class Meta:
        model = UserApplication
        django_get_or_create = ('user',)

    user = factory.SubFactory(UserFactory)
    business_line = factory.SubFactory(BusinessLineFactory)
    organization = 'testOrganization'


class ApplicationHubFactory(factory.DjangoModelFactory):
    """
    Factory for ApplicationHub Model
    """

    class Meta:
        model = ApplicationHub
        django_get_or_create = ('user',)

    user = factory.SubFactory(UserFactory)


class EducationFactory(factory.DjangoModelFactory):
    """
    Factory for Education model
    """

    class Meta:
        model = Education

    user_application = factory.SubFactory(UserApplicationFactory)
    name_of_school = factory.Faker('word')
    degree = Education.BACHELOR_DEGREE
    area_of_study = factory.Faker('sentence')
    date_started_month = 1
    date_started_year = 2018
    date_completed_month = 1
    date_completed_year = 2020


class WorkExperienceFactory(factory.DjangoModelFactory):
    """
    Factory for Work experience model
    """

    class Meta:
        model = WorkExperience

    user_application = factory.SubFactory(UserApplicationFactory)
    name_of_organization = factory.Faker('word')
    job_position_title = factory.Faker('word')
    job_responsibilities = factory.Faker('sentence')
    date_started_month = 1
    date_started_year = 2018
    date_completed_month = 1
    date_completed_year = 2020


class MultilingualCourseGroupFactory(factory.DjangoModelFactory):
    """
    Factory for Work experience model
    """

    name = factory.Sequence(lambda n: 'Course group #%s' % n)
    is_program_prerequisite = True
    is_common_business_line_prerequisite = False

    class Meta:
        model = MultilingualCourseGroup


class MultilingualCourseFactory(factory.DjangoModelFactory):
    """
    Factory for Multilingual Course
    """

    course = factory.SubFactory(CourseOverviewFactory)
    multilingual_course_group = factory.SubFactory(MultilingualCourseGroupFactory)

    class Meta:
        model = MultilingualCourse
        django_get_or_create = ('course', 'multilingual_course_group')


class ReferenceFactory(factory.DjangoModelFactory):
    """
    Factory for Reference model
    """

    class Meta:
        model = Reference
