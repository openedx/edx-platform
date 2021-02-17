"""
Helper functions required for tests
"""
import hashlib
from datetime import datetime, timedelta

from django.conf import settings

from lms.djangoapps.onboarding.models import OrganizationPartner
from lms.djangoapps.onboarding.tests.factories import OrganizationFactory


def create_organization(user):
    """
    create and return organization with given user as an organization admin
    :param user: organization admin user
    :return: created organization
    """
    organization = OrganizationFactory(
        admin=user,
        alternate_admin_email=user.email,
        label='test_org'
    )
    organization.save()
    return organization


def create_organization_partner_object(user):
    """
    create and return organization partner with given user as an organization admin
    :param user: organization admin user
    :return: created organization partner
    """
    organization = create_organization(user)
    partner = OrganizationPartner(
        organization=organization,
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=1),
        partner='ECHIDNA'
    )
    partner.save()
    return partner


def generate_mailchimp_url(root_url, email):
    """
    Convert email into encrypted email hash
    :param root_url: MailChimp root URL
    :param email: MailChimp user email
    :return: formatted path with url and email hash
    """
    list_id = settings.MAILCHIMP_LEARNERS_LIST_ID
    hashlib_md = hashlib.md5()
    hashlib_md.update(email.lower())
    email_hash = hashlib_md.hexdigest()
    path = '{root_url}/lists/{list_id}/members/{subscriber_hash}'.format(
        root_url=root_url, list_id=list_id, subscriber_hash=email_hash)
    return path
