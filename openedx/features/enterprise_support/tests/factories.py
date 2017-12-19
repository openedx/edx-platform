"""
Factoryboy factories.
"""
from __future__ import absolute_import, unicode_literals

from uuid import UUID

import factory
from faker import Factory as FakerFactory

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory

from enterprise.models import (
    EnterpriseCustomer,
    EnterpriseCustomerUser,
)

FAKER = FakerFactory.create()


class EnterpriseCustomerFactory(factory.django.DjangoModelFactory):
    """
    EnterpriseCustomer factory.

    Creates an instance of EnterpriseCustomer with minimal boilerplate - uses this class' attributes as default
    parameters for EnterpriseCustomer constructor.
    """

    class Meta(object):
        """
        Meta for EnterpriseCustomerFactory.
        """

        model = EnterpriseCustomer

    uuid = factory.LazyAttribute(lambda x: UUID(FAKER.uuid4()))  # pylint: disable=no-member
    name = factory.LazyAttribute(lambda x: FAKER.company())  # pylint: disable=no-member
    active = True
    site = factory.SubFactory(SiteFactory)
    catalog = factory.LazyAttribute(lambda x: FAKER.random_int(min=0, max=1000000))  # pylint: disable=no-member
    enable_data_sharing_consent = True
    enforce_data_sharing_consent = EnterpriseCustomer.AT_ENROLLMENT


class EnterpriseCustomerUserFactory(factory.django.DjangoModelFactory):
    """
    EnterpriseCustomer factory.

    Creates an instance of EnterpriseCustomerUser with minimal boilerplate - uses this class' attributes as default
    parameters for EnterpriseCustomerUser constructor.
    """

    class Meta(object):
        """
        Meta for EnterpriseCustomerFactory.
        """

        model = EnterpriseCustomerUser

    enterprise_customer = factory.SubFactory(EnterpriseCustomerFactory)
    user_id = factory.LazyAttribute(lambda x: FAKER.pyint())  # pylint: disable=no-member
