"""
Testing multi-tenant CERTIFICATES_HTML_VIEW feature flag.
"""
import pytest
from organizations.models import OrganizationCourse

from cms.djangoapps.contentstore.views.certificates import CertificateManager
from openedx.core.djangoapps.appsembler.api.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.appsembler.multi_tenant_emails.tests.test_utils import with_organization_context

from tahoe_sites.api import get_site_by_organization


@pytest.fixture
def create_course_with_site_configuration(settings):
    """
    Factory for course with its related site configuration.
    """
    def _create_course_with_site_configuration(configs):
        # Ensure SiteConfiguration.save() works
        settings.DEFAULT_SITE_THEME = 'edx-theme-codebase'
        course = CourseOverviewFactory.create()
        # Simulate configured certificates in the course
        course.certificates = {'certificates': [{'is_active': True}]}

        with with_organization_context(site_color=course.org, configs=configs) as organization:
            site = get_site_by_organization(organization)

        # Link the course to the organization
        OrganizationCourse.objects.create(course_id=course.id, organization=organization)

        return {
            'course': course,
            'site_configuration': site.configuration,
            'site': site,
            'organization': organization,
        }

    return _create_course_with_site_configuration


@pytest.mark.django_db
@pytest.mark.parametrize('feature_flag', [False, True])
def test_html_certificate_feature_flag_enabled(feature_flag, create_course_with_site_configuration):
    """
    Ensure CERTIFICATES_HTML_VIEW can be enabled via SiteConfiguration.
    """
    course_data = create_course_with_site_configuration({
        'CERTIFICATES_HTML_VIEW': feature_flag
    })
    course = course_data['course']

    is_active, _certificates = CertificateManager.is_activated(course=course)
    assert is_active == feature_flag, 'Should match the feature flag.'
