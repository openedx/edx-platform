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
from openedx.features.edly.models import EdlyOrganization, EdlySubOrganization, EdlyUserProfile
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
    lms_site = SubFactory(SiteFactory)
    studio_site = SubFactory(SiteFactory)


class EdlyUserFactory(UserFactory):
    """
    Factory inherit from "UserFactory" of edx.
    """

    class Meta(object):
        model = User

    @factory.post_generation
    def profile(obj, create, extracted, **kwargs):
        if create:
            obj.save()
            return EdlyUserProfileFactory.create(user=obj, **kwargs)
        elif kwargs:
            raise Exception('Cannot build a user edly profile without saving the user')
        else:
            return None


class EdlyUserProfileFactory(DjangoModelFactory):
    """
    Factory class for "EdlyUserProfile" model.
    """
    class Meta(object):
        model = EdlyUserProfile
        django_get_or_create = ('user', )

    user = SubFactory(EdlyUserFactory)

    @factory.post_generation
    def edly_sub_organizations(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for edly_sub_org in extracted:
                self.edly_sub_organizations.add(edly_sub_org)
