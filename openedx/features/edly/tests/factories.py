"""
Model factories for unit testing views or models.
"""
import factory
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from factory import SelfAttribute, Sequence, SubFactory
from factory.django import DjangoModelFactory
from organizations.tests.factories import OrganizationFactory

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.features.edly.models import EdlyMultiSiteAccess, EdlyOrganization, EdlySubOrganization
from student.tests.factories import UserFactory


class EdlyOrganizationFactory(DjangoModelFactory):
    """
    Factory class for "EdlyOrganization" model.
    """

    class Meta(object):
        model = EdlyOrganization
        django_get_or_create = ('name', 'slug')

    name = Sequence('Edly Organization {}'.format)
    slug = Sequence('edly-organization-{}'.format)


class EdlySubOrganizationFactory(DjangoModelFactory):
    """
    Factory class for "EdlySubOrganization" model.
    """

    class Meta(object):
        model = EdlySubOrganization
        django_get_or_create = ('name', 'slug')

    name = Sequence('Edly SubOrganization {}'.format)
    slug = Sequence('edly-sub-organization-{}'.format)
    edly_organization = SubFactory(EdlyOrganizationFactory)
    edx_organization = SubFactory(OrganizationFactory)
    edx_organizations = SubFactory(OrganizationFactory)
    lms_site = SubFactory(SiteFactory)
    studio_site = SubFactory(SiteFactory)
    is_active = True

    @factory.post_generation
    def edx_organizations(self, create, extracted, **kwargs):
        """
        EdX organizations post generation method.
        """
        # pylint: disable=no-member,unused-argument
        if not create:
            return

        if extracted:
            edx_orgs = []
            edx_orgs.extend(extracted if isinstance(extracted, list) else [extracted])
            for edx_org in edx_orgs:
                self.edx_organizations.add(edx_org)
        else:
            self.edx_organizations.add(self.edx_organization)


class EdlyMultiSiteAccessFactory(DjangoModelFactory):
    """
    Factory class for "EdlyMultiSiteAccess" model.
    """
    class Meta(object):
        model = EdlyMultiSiteAccess

    user = SubFactory(UserFactory)
    sub_org = SubFactory(EdlySubOrganizationFactory)
