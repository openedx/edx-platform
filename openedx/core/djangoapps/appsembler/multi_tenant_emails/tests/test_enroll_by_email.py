"""
Tests for the `CourseEnrollment.enroll_by_email` method with `APPSEMBLER_MULTI_TENANT_EMAILS`.
"""

import pytest

from django.contrib.auth import get_user_model
from student.models import CourseEnrollment

from openedx.core.djangoapps.appsembler.api.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.appsembler.multi_tenant_emails.tests.test_utils import (
    create_org_user,
    with_organization_context,
)

User = get_user_model()


@pytest.mark.django_db
def test_enroll_by_email_single_tenant(settings):
    """
    Ensure `enroll_by_email` works as upstream intended if APPSEMBLER_MULTI_TENANT_EMAILS is disabled.
    """
    settings.FEATURES = {'APPSEMBLER_MULTI_TENANT_EMAILS': False}
    course = CourseOverviewFactory.create()
    course_key = course.id

    with with_organization_context(site_color='blue1') as blue_org:
        blue_user = create_org_user(blue_org)

    with with_organization_context(site_color='red1') as red_org:
        red_user = create_org_user(red_org)

        assert CourseEnrollment.enroll_by_email(red_user.email, course_key), 'Should enroll in same site'
        assert CourseEnrollment.is_enrolled(red_user, course_key)

        assert CourseEnrollment.enroll_by_email(blue_user.email, course_key), 'Should enroll in other sites'
        assert CourseEnrollment.is_enrolled(blue_user, course_key)


@pytest.mark.django_db
def test_enroll_by_email_multi_tenant(settings):
    """
    Ensure `enroll_by_email` works with APPSEMBLER_MULTI_TENANT_EMAILS is enabled.
    """
    settings.FEATURES = {'APPSEMBLER_MULTI_TENANT_EMAILS': True}
    course = CourseOverviewFactory.create()
    course_key = course.id

    with with_organization_context(site_color='blue1') as blue_org:
        blue_user = create_org_user(blue_org)

    with with_organization_context(site_color='red1') as red_org:
        red_user = create_org_user(red_org)

        assert CourseEnrollment.enroll_by_email(red_user.email, course_key), 'Should enroll in same site'
        assert CourseEnrollment.is_enrolled(red_user, course_key)

        assert not CourseEnrollment.enroll_by_email(blue_user.email, course_key), 'Should not enroll in other sites'
        assert not CourseEnrollment.is_enrolled(blue_user, course_key), 'Should not enroll in other sites'
