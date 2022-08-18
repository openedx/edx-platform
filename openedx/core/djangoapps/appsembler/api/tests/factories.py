
import datetime

import factory
import factory.fuzzy

from openedx.core.djangoapps.content.course_overviews.models import (
    CourseOverview,
)
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

from openedx.core.djangoapps.site_configuration.tests.factories import (
    SiteFactory,
)

import organizations
from tahoe_sites.api import create_tahoe_site_by_link

from openedx.core.djangoapps.appsembler.api.helpers import as_course_key


COURSE_ID_STR_TEMPLATE = 'course-v1:StarFleetAcademy+SFA{}+2161'


class CourseOverviewFactory(factory.DjangoModelFactory):
    class Meta:
        model = CourseOverview

    # Only define the fields that we will retrieve
    id = factory.Sequence(lambda n: as_course_key(
        COURSE_ID_STR_TEMPLATE.format(n)))
    display_name = factory.Sequence(lambda n: 'SFA Course {}'.format(n))
    org = 'StarFleetAcademy'
    version = CourseOverview.VERSION
    display_org_with_default = factory.LazyAttribute(lambda o: o.org)
    created = factory.fuzzy.FuzzyDateTime(datetime.datetime(
        2018, 2, 1, tzinfo=factory.compat.UTC))
    enrollment_start = factory.fuzzy.FuzzyDateTime(datetime.datetime(
        2018, 3, 1, tzinfo=factory.compat.UTC))
    enrollment_end = factory.fuzzy.FuzzyDateTime(datetime.datetime(
        2018, 3, 15, tzinfo=factory.compat.UTC))
    start = factory.fuzzy.FuzzyDateTime(datetime.datetime(
        2018, 4, 1, tzinfo=factory.compat.UTC))
    end = factory.fuzzy.FuzzyDateTime(datetime.datetime(
        2018, 6, 1, tzinfo=factory.compat.UTC))
    self_paced = False


class SiteConfigurationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = SiteConfiguration

    site = factory.SubFactory(SiteFactory)
    enabled = True
    site_values = {
        'PLATFORM_NAME': factory.SelfAttribute('site.name'),
        'SITE_NAME': factory.SelfAttribute('site.domain'),
    }
    sass_variables = {}
    page_elements = {}


class OrganizationFactory(factory.DjangoModelFactory):
    """
    We define the OrganizationFactory here instead of using the one in
    edx-organizations because that one is missing the `sites` relationship and
    we can't rely on getting `organizations.tests` to simply extend
    organizations/tests/factories.py:OrganizationFactory
    """
    class Meta(object):
        model = organizations.models.Organization

    name = factory.Sequence('organization name {}'.format)
    short_name = factory.Sequence('name{}'.format)
    description = factory.Sequence('description{}'.format)
    logo = None
    active = True

    @factory.post_generation
    def linked_site(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            create_tahoe_site_by_link(organization=self, site=extracted)


class OrganizationCourseFactory(factory.DjangoModelFactory):
    class Meta:
        model = organizations.models.OrganizationCourse

    course_id = factory.Sequence(lambda n: COURSE_ID_STR_TEMPLATE.format(n))
    organization = factory.SubFactory(OrganizationFactory)
    active = True
