import factory
from factory.django import DjangoModelFactory
from faker.providers import internet

from lms.djangoapps.onboarding.models import FocusArea, Organization
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.features.course_card.models import CourseCard
from openedx.features.partners.models import Partner, PartnerCommunity, PartnerUser
from student.tests.factories import UserFactory

factory.Faker.add_provider(internet)


class PartnerFactory(DjangoModelFactory):
    class Meta:
        model = Partner

    performance_url = factory.Faker('url')
    label = factory.Faker('name')
    slug = factory.Faker('slug')
    logo = 'dummy'
    email = 'dummy'
    configuration = {'USER_LIMIT': None}


class PartnerUserFactory(DjangoModelFactory):
    class Meta:
        model = PartnerUser

    partner = factory.SubFactory(PartnerFactory)
    user = factory.SubFactory(UserFactory)


class PartnerCourseOverviewFactory(CourseOverviewFactory):
    display_name = factory.Faker('word')
    # enrollment start date is less than current date
    enrollment_start = factory.Faker('date_time_between', start_date='-10d', end_date='now')
    # enrollment end date greater than current date
    enrollment_end = factory.Faker('date_time_between', start_date='+1d', end_date='+10d')


class CourseCardFactory(DjangoModelFactory):
    class Meta:
        model = CourseCard

    is_enabled = True
    course_name = factory.Faker('word')


class PartnerCommunityFactory(DjangoModelFactory):
    class Meta:
        model = PartnerCommunity

    community_id = factory.Sequence(lambda n: n)


class FocusAreaFactory(DjangoModelFactory):
    class Meta:
        model = FocusArea

    order = factory.Sequence(lambda n: n)
    code = 'IWRNS'
    label = factory.Faker('word')


class OrganizationFactory(DjangoModelFactory):
    class Meta(object):
        model = Organization
        django_get_or_create = ('label',)

    label = factory.Sequence(u'Organization{0}'.format)
    country = factory.Faker('country')
    city = factory.Faker('city')
    founding_year = factory.Faker('random_int')
    org_type = 'IWRNS'
    level_of_operation = 'dummy'
    total_employees = 'dummy'
