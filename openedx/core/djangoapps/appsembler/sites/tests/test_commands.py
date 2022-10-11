import hashlib
import os
from unittest.mock import patch, mock_open, Mock
from io import StringIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings, TestCase

from tahoe_sites.api import (
    create_tahoe_site_by_link,
    get_organization_for_user,
    get_users_of_organization,
    get_uuid_by_organization,
    get_organization_by_site,
)
from tahoe_sites.tests.utils import create_organization_mapping

from openedx.core.djangoapps.appsembler.sites.management.commands.create_devstack_site import Command
from openedx.core.djangoapps.appsembler.sites.management.commands.offboard import Command as OffboardSiteCommand
from openedx.core.djangoapps.appsembler.sites.models import AlternativeDomain
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration, SiteConfigurationHistory
from openedx.core.djangoapps.theming.models import SiteTheme
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from openedx.core.djangoapps.appsembler.api.tests.factories import (
    CourseOverviewFactory,
    OrganizationFactory,
    OrganizationCourseFactory,
)
from openedx.core.djangoapps.appsembler.sites.tests.factories import (
    AlternativeDomainFactory,
)
from openedx.core.djangoapps.site_configuration.tests.factories import (
    SiteFactory,
)
from student.models import (
    CourseAccessRole,
    CourseEnrollment,
    CourseEnrollmentAllowed,
    LanguageProficiency,
    ManualEnrollmentAudit,
    SocialLink,
    UserAttribute,
    UserSignupSource,
    UserTestGroup,
)
from student.tests.factories import (
    CourseAccessRoleFactory,
    CourseEnrollmentAllowedFactory,
    CourseEnrollmentFactory,
    UserFactory,
    UserStandingFactory,
)

from organizations.models import Organization, OrganizationCourse

from oauth2_provider.models import AccessToken, RefreshToken, Application

from student.roles import CourseCreatorRole


@override_settings(
    DEBUG=True,
    DEFAULT_SITE_THEME='edx-theme-codebase',
)
@patch.dict('django.conf.settings.FEATURES', {
    'DISABLE_COURSE_CREATION': False,
    'ENABLE_CREATOR_GROUP': True,
})
class CreateDevstackSiteCommandTestCase(TestCase):
    """
    Test ./manage.py lms create_devstack_site mydevstack
    """
    name = 'mydevstack'  # Used for both username, email and domain prefix.
    site_name = '{}.localhost:18000'.format(name)

    def setUp(self):
        assert settings.ENABLE_COMPREHENSIVE_THEMING
        Application.objects.create(client_id=settings.AMC_APP_OAUTH2_CLIENT_ID,
                                   client_type=Application.CLIENT_CONFIDENTIAL)

    def test_no_sites(self):
        """
        Ensure nothing exists prior to the site creation.

        If something exists, it means Open edX have changed something in the sites so this
        test needs to be refactored.
        """
        assert not Site.objects.filter(domain=self.site_name).count()
        assert not Organization.objects.count()
        assert not get_user_model().objects.count()

    def test_create_devstack_site(self):
        """
        Test that `create_devstack_site` and creates the required objects.
        """
        with patch.object(Command, 'congrats') as mock_congrats:
            call_command('create_devstack_site', self.name, 'localhost')

        assert mock_congrats.called  # Ensure that congrats message is printed
        assert mock_congrats.call_count == 1  # Ensure that congrats message is printed once

        # Ensure objects are created correctly.
        assert Site.objects.get(domain=self.site_name)
        organization = Organization.objects.get(name=self.name)
        user = get_user_model().objects.get()
        assert user.check_password(self.name)
        assert user.profile.name == self.name
        assert get_organization_for_user(user=user) == organization

        assert CourseCreatorRole().has_user(user), 'User should be a course creator'

        fake_token = hashlib.md5(user.username.encode('utf-8')).hexdigest()  # Using a fake token so AMC devstack can guess it
        assert fake_token == '80bfa968ffad007c79bfc603f3670c99', 'Ensure hash is identical to AMC'
        assert AccessToken.objects.get(user=user).token == fake_token, 'Access token is needed'
        assert RefreshToken.objects.get(user=user).token == fake_token, 'Refresh token is needed'


@override_settings(
    DEBUG=True,
)
class TestCandidateSitesCleanupCommand(TestCase):
    """
    Tests for the `danger_candidate_sites_cleanup` management command.
    """
    def setUp(self):
        Application.objects.create(client_id=settings.AMC_APP_OAUTH2_CLIENT_ID,
                                   client_type=Application.CLIENT_CONFIDENTIAL)
        call_command('create_devstack_site', 'blue', 'oldlocalhost')
        site_config = self.get_site().configuration
        site_config.site_values.update({
            'SEGMENT_KEY': 'test1',
            'customer_gtm_id': 'test2',
        })
        site_config.save()

    def get_site(self):
        return Site.objects.get(domain__startswith='blue.')

    def test_run(self):
        assert self.get_site().domain == 'blue.oldlocalhost:18000'
        active_orgs = Organization.objects.all()
        active_orgs_function_path = 'openedx.core.djangoapps.appsembler.sites.utils.get_active_organizations'
        with patch(active_orgs_function_path, return_value=active_orgs):
            # Side-step the `Tier` model.
            call_command('danger_candidate_sites_cleanup', 'oldlocalhost:18000', 'newlocalhost:18000')
        assert self.get_site().domain == 'blue.newlocalhost:18000'
        assert not self.get_site().configuration.get_value('customer_gtm_id')
        assert not self.get_site().configuration.get_value('SEGMENT_KEY')
        assert self.get_site().configuration.get_value('SITE_NAME') == self.get_site().domain


@override_settings(
    DEBUG=True,
    DEFAULT_SITE_THEME='edx-theme-codebase',
)
@patch.dict('django.conf.settings.FEATURES', {
    'DISABLE_COURSE_CREATION': False,
    'ENABLE_CREATOR_GROUP': True,
})
@patch(  # Avoid CMS-related import issues in tests
    'openedx.core.djangoapps.appsembler.sites.utils.remove_course_creator_role',
    Mock()
)
class RemoveSiteCommandTestCase(TestCase):
    """
    Test ./manage.py lms remove_site mysite
    """
    def setUp(self):
        assert settings.ENABLE_COMPREHENSIVE_THEMING
        Application.objects.create(client_id=settings.AMC_APP_OAUTH2_CLIENT_ID,
                                   client_type=Application.CLIENT_CONFIDENTIAL)

        self.to_be_deleted = 'delete'
        self.shall_remain = 'keep'

        # This command should be tested above
        call_command('create_devstack_site', self.to_be_deleted, 'localhost')
        call_command('create_devstack_site', self.shall_remain, 'localhost')

    def test_remove_devstack_site_commit(self):
        """
        Test that `remove_site` and removes the site _with_ commit.
        """
        deleted_domain = '{}.localhost:18000'.format(self.to_be_deleted)
        remained_domain = '{}.localhost:18000'.format(self.shall_remain)
        assert SiteConfiguration.objects.count() == 2, 'there are two sites'
        remained_site = Site.objects.get(domain=remained_domain)

        # TODO: Re-produce the error we face in staging
        to_delete_site = Site.objects.get(domain=deleted_domain)
        to_delete_organization = get_organization_by_site(to_delete_site)
        users = get_users_of_organization(to_delete_organization)
        assert len(users), 'Ensure the site has users'
        call_command('remove_site', deleted_domain, commit=True)

        # Ensure objects are removed correctly.
        assert not Site.objects.filter(domain=deleted_domain).exists()

        assert SiteConfiguration.objects.count() == 1, 'One site is deleted'
        assert SiteConfiguration.objects.get(site=remained_site), 'remained_domain site config is kept'

        assert SiteTheme.objects.filter(site=remained_site).count() == remained_site.themes.count()

    def test_remove_devstack_site_rollback(self):
        """
        Test that `remove_site` do not remove the site _without_ committing.
        """
        deleted_domain = '{}.localhost:18000'.format(self.to_be_deleted)
        call_command('remove_site', deleted_domain)
        assert Site.objects.filter(domain=deleted_domain).exists()


class TestOffboardSiteCommand(ModuleStoreTestCase):
    """
    Test ./manage.py lms offboard site.domain.com
    """

    def setUp(self):
        super(TestOffboardSiteCommand, self).setUp()

        self.site_name = 'site'
        self.site_domain = '{}.localhost:18000'.format(self.site_name)

        self.site = Site.objects.create(domain=self.site_domain, name=self.site_name)
        create_tahoe_site_by_link(site=self.site, organization=OrganizationFactory())
        SiteConfigurationFactory.create(site=self.site)

        self.command = OffboardSiteCommand()

    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.write_to_file', return_value='called')
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.check')
    def test_handle(self, mock_check, mock_write_to_file):
        out = StringIO()
        call_command('offboard', self.site_domain, stdout=out)

        assert mock_check.called
        assert mock_write_to_file.called

        assert 'Offboarding "%s" in progress' % self.site_domain in out.getvalue()
        assert 'Successfully offboarded' in out.getvalue()
        assert 'Command output >>>' not in out.getvalue()

    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.write_to_file', return_value='called')
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.check')
    def test_handle_debug(self, mock_check, mock_write_to_file):
        out = StringIO()
        call_command('offboard', self.site_domain, debug=True, stdout=out)

        assert mock_check.called
        assert mock_write_to_file.called

        assert 'Offboarding "%s" in progress' % self.site_domain in out.getvalue()
        assert 'Command output >>>' in out.getvalue()
        assert 'Successfully offboard' in out.getvalue()

    def test_handle_system_check_fails(self):
        """
        According to Django, serious problems are raised as a CommandError wheb calling
        this `check` function. Proccessing should stop in case we got a serious problem.

        https://docs.djangoproject.com/en/1.11/howto/custom-management-commands/#django.core.management.BaseCommand.check
        """

        with patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.check', side_effect=CommandError()):
            with self.assertRaises(CommandError):
                call_command('offboard', self.site_domain, debug=True)
            with self.assertRaises(CommandError):
                call_command('offboard', self.site_domain)

    def test_generate_file_path(self):
        # With output.json
        output = 'new_file.json'
        path = self.command.generate_file_path(self.site, output)
        assert path == output

        # With output
        output = 'new_file'
        path = self.command.generate_file_path(self.site, output)
        assert path.endswith('.json')
        assert path.startswith('%s/' % output)

        # With no output
        path = self.command.generate_file_path(self.site, None)
        assert path.endswith('.json')
        assert path.startswith('%s/' % os.getcwd())

    def test_get_site(self):
        assert self.site == self.command.get_site(self.site_domain)

        with self.assertRaises(CommandError):
            self.command.get_site('invailed-domain')

    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_site', return_value='process_site')
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_organization', return_value=[])
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_courses', return_value=[])
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_site_configurations', return_value={})
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_site_configurations_history', return_value=[])
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_users', return_value=[])
    def test_generate_objects(self, mock1, mock2, mock3, mock4, mock5, mock6):
        data = self.command.generate_objects(self.site)
        assert data == {
            'site': 'process_site',
            'organizations': [[]],
            'courses': [],
            'configurations': {},
            'configurations_history': [],
            'users': [],
        }

    def test_process_site(self):
        data = self.command.process_site(self.site)
        assert data == {
            'name': self.site.name,
            'domain': self.site.domain,
        }

    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_organization_users', return_value=['user1', 'user2'])
    def test_process_organization(self, mock_process_organization_users):
        site = SiteFactory(domain='test')
        organization = OrganizationFactory.create(name='test')
        create_tahoe_site_by_link(organization=organization, site=site)
        data = self.command.process_organization(organization)
        assert data == {
            'name': organization.name,
            'short_name': organization.short_name,
            'description': organization.description,
            'logo': '',
            'active': organization.active,
            'UUID': get_uuid_by_organization(organization=organization),
            'created': organization.created,
            'users': ['user1', 'user2']
        }

    def test_process_organization_users(self):
        organization = OrganizationFactory.create(name='test')
        new_user_count = 3

        assert get_users_of_organization(organization=organization).count() == 0
        self.create_org_users(org=organization, new_user_count=new_user_count)
        assert get_users_of_organization(organization=organization).count() == new_user_count

        data = self.command.process_organization_users(organization)
        assert len(data) == new_user_count
        assert data == [{
            'username': user.username,
            'active': user.is_active,
        } for user in get_users_of_organization(organization=organization).all()]

    def test_process_site_configurations(self):
        data = self.command.process_site_configurations(self.site)
        site_configs = SiteConfiguration.objects.get(site=self.site)

        assert data == {
            'enabled': site_configs.enabled,
            'values': site_configs.site_values,
            'sass_variables': site_configs.sass_variables,
            'page_elements': site_configs.page_elements,
        }

    def test_process_site_configurations_history(self):
        data = self.command.process_site_configurations_history(self.site)
        assert data == [
            {
                'enabled': record.enabled,
                'values': record.site_values,
            } for record in SiteConfigurationHistory.objects.filter(site=self.site)
        ]

    def test_process_course_overview(self):
        empty_data = self.command.process_course_overview(None)
        assert empty_data == {}

        course_overview = CourseOverviewFactory()
        data = self.command.process_course_overview(course_overview)
        assert data == {
            'version': course_overview.version,
            'org': course_overview.org,
            'display_name': course_overview.display_name,
            'display_number_with_default': course_overview.display_number_with_default,
            'display_org_with_default': course_overview.display_org_with_default,
            'start': course_overview.start,
            'end': course_overview.end,
            'advertised_start': course_overview.advertised_start,
            'announcement': course_overview.announcement,
            'course_image_url': course_overview.course_image_url,
            'social_sharing_url': course_overview.social_sharing_url,
            'end_of_course_survey_url': course_overview.end_of_course_survey_url,
            'certificates_display_behavior': course_overview.certificates_display_behavior,
            'certificates_show_before_end': course_overview.certificates_show_before_end,
            'cert_html_view_enabled': course_overview.cert_html_view_enabled,
            'has_any_active_web_certificate': course_overview.has_any_active_web_certificate,
            'cert_name_short': course_overview.cert_name_short,
            'cert_name_long': course_overview.cert_name_long,
            'certificate_available_date': course_overview.certificate_available_date,
            'lowest_passing_grade': course_overview.lowest_passing_grade,
            'days_early_for_beta': course_overview.days_early_for_beta,
            'mobile_available': course_overview.mobile_available,
            'visible_to_staff_only': course_overview.visible_to_staff_only,
            'pre_requisite_courses_json': course_overview._pre_requisite_courses_json,
            'enrollment_start': course_overview.enrollment_start,
            'enrollment_end': course_overview.enrollment_end,
            'enrollment_domain': course_overview.enrollment_domain,
            'invitation_only': course_overview.invitation_only,
            'max_student_enrollments_allowed': course_overview.max_student_enrollments_allowed,
            'catalog_visibility': course_overview.catalog_visibility,
            'short_description': course_overview.short_description,
            'course_video_url': course_overview.course_video_url,
            'effort': course_overview.effort,
            'self_paced': course_overview.self_paced,
            'marketing_url': course_overview.marketing_url,
            'eligible_for_financial_aid': course_overview.eligible_for_financial_aid,
            'language': course_overview.language,
        }

    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_enrollment_audit', return_value=[])
    def test_process_enrollments(self, mock):
        course_overview = CourseOverviewFactory()
        enrollment = CourseEnrollmentFactory(course=course_overview)

        data = self.command.process_enrollments(course_overview)
        assert data == [{
            'user': enrollment.user.username,
            'created': enrollment.created,
            'active': enrollment.is_active,
            'mode': enrollment.mode,
            'audit': []
        }]

    def test_process_user_profile(self):
        user = UserFactory()
        data = self.command.process_user_profile(user)
        profile = user.profile

        assert data == {
            'name': profile.name,
            'courseware': profile.courseware,
            'language': profile.language,
            'location': profile.location,
            'year_of_birth': profile.year_of_birth,
            'gender': profile.gender_display,
            'level_of_education': profile.level_of_education_display,
            'mailing_address': profile.mailing_address,
            'city': profile.city,
            'country': profile.country.name if profile.country else '',
            'goals': profile.goals,
            'allow_certificate': profile.allow_certificate,
            'bio': profile.bio,
            'profile_image_uploaded_at': profile.profile_image_uploaded_at,
        }

    def test_process_user_standing(self):
        user = UserFactory()
        empty_data = self.command.process_user_standing(user)

        assert empty_data == {}
        from student.models import UserStanding

        standing = UserStandingFactory.create(
            user=user,
            account_status=UserStanding.ACCOUNT_DISABLED,
            changed_by=user
        )
        data = self.command.process_user_standing(user)

        assert data == {
            'account_status': standing.account_status,
            'changed_by': standing.changed_by.username,
            'standing_last_changed_at': standing.standing_last_changed_at,
        }

    def test_process_user_test_groups(self):
        test_group = UserTestGroup.objects.create(name='test', description='test')
        user = UserFactory()

        test_group.users.add(user)
        test_group.save()

        data = self.command.process_user_test_groups(user)
        assert data == [{
            'name': test_group.name,
            'description': test_group.description,
        }]

    def test_process_user_languages(self):
        user = UserFactory()
        languages_qs = LanguageProficiency.objects.filter(user_profile=user.profile)
        assert languages_qs.count() == 0

        LanguageProficiency.objects.create(
            user_profile=user.profile,
            code='AR'
        )
        LanguageProficiency.objects.create(
            user_profile=user.profile,
            code='EN'
        )

        data = self.command.process_user_languages(user)

        languages_qs = LanguageProficiency.objects.filter(user_profile=user.profile)
        assert languages_qs.count() == 2
        assert data == [language.code for language in languages_qs]

    def test_process_social_links(self):
        user = UserFactory()

        social_links_qs = SocialLink.objects.filter(user_profile=user.profile)
        assert social_links_qs.count() == 0

        SocialLink.objects.create(
            user_profile=user.profile,
            platform='facebook',
            social_link='https://www.facebook.com/username'
        )
        SocialLink.objects.create(
            user_profile=user.profile,
            platform='twitter',
            social_link='https://www.twitter.com/username'
        )

        social_links_qs = SocialLink.objects.filter(user_profile=user.profile)
        assert social_links_qs.count() == 2

        data = self.command.process_social_links(user)
        assert data == [{
            'platform': link.platform,
            'social_link': link.social_link,
        } for link in social_links_qs]

    def test_process_attributes(self):
        user = UserFactory()

        user_attributes_qs = UserAttribute.objects.filter(user=user)
        assert user_attributes_qs.count() == 0

        UserAttribute.objects.create(user=user, name='test1', value='test1')
        UserAttribute.objects.create(user=user, name='test2', value='test2')

        user_attributes_qs = UserAttribute.objects.filter(user=user)
        assert user_attributes_qs.count() == 2

        data = self.command.process_attributes(user)
        assert data == [{
            'name': attribute.name,
            'value': attribute.value,
        } for attribute in user_attributes_qs]

    def test_process_access_roles(self):
        course = CourseFactory.create()
        access_roles_count = 3

        access_roles_qs = CourseAccessRole.objects.filter(course_id=course.id)
        assert access_roles_qs.count() == 0

        for _ in range(access_roles_count):
            CourseAccessRoleFactory(course_id=course.id, user=UserFactory.create(), role='Wizard')

        access_roles_qs = CourseAccessRole.objects.filter(course_id=course.id)
        assert access_roles_qs.count() == access_roles_count

        data = self.command.process_access_roles(course.id)
        assert len(data) == access_roles_count
        assert data == [{
            'user': role.user.username,
            'org': role.org,
            'role': role.role,
        } for role in access_roles_qs]

    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_attributes', return_value={})
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_social_links', return_value=[])
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_user_languages', return_value=[])
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_user_test_groups', return_value={})
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_user_standing', return_value={})
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_user_profile', return_value={})
    def test_process_users(self, mock1, mock2, mock3, mock4, mock5, mock6):
        users_count = 3

        signup_source_qs = UserSignupSource.objects.filter(site=self.site)
        assert signup_source_qs.count() == 0

        for _ in range(users_count):
            UserSignupSource.objects.create(user=UserFactory(), site=self.site)

        signup_source_qs = UserSignupSource.objects.filter(site=self.site)
        assert signup_source_qs.count() == users_count

        data = self.command.process_users(self.site)
        assert len(data) == users_count
        assert data == [{
            'user_name': source.user.username,
            'first_name': source.user.first_name,
            'last_name': source.user.last_name,
            'active': source.user.is_active,
            'last_login': source.user.last_login,
            'permissions': [permission for permission in source.user.user_permissions.all()],
            'date_joined': source.user.date_joined,
            'profile': {},
            'standing': {},
            'test_groups': {},
            'languages': [],
            'social_links': [],
            'attributes': {},
        } for source in signup_source_qs]

    def test_process_enrollment_allowed(self):
        allowed_enrollments_count = 3
        course = CourseFactory.create()
        enrollment_allowed_qs = CourseEnrollmentAllowed.objects.filter(course_id=course.id)

        assert enrollment_allowed_qs.count() == 0

        for _ in range(allowed_enrollments_count):
            CourseEnrollmentAllowedFactory(email=UserFactory().email, course_id=course.id)

        enrollment_allowed_qs = CourseEnrollmentAllowed.objects.filter(course_id=course.id)
        assert enrollment_allowed_qs.count() == allowed_enrollments_count

        data = self.command.process_enrollment_allowed(course.id)
        assert len(data) == allowed_enrollments_count
        assert data == [{
            'email': record.email,
            'auto_enroll': record.auto_enroll,
            'user': record.user.username if record.user else None,
            'created': record.created,
        } for record in enrollment_allowed_qs]

    def test_process_enrollment_audit(self):
        audit_count = 3
        course = CourseFactory()
        enrollment = CourseEnrollment.enroll(user=UserFactory(), course_key=course.id)

        enrollment_audits = ManualEnrollmentAudit.objects.filter(enrollment=enrollment)
        assert enrollment_audits.count() == 0

        for _ in range(audit_count):
            ManualEnrollmentAudit.objects.create(
                enrollment=enrollment,
                reason='PII here',
                enrolled_email=UserFactory().email,
                enrolled_by=UserFactory()
            )

        enrollment_audits = ManualEnrollmentAudit.objects.filter(enrollment=enrollment)
        assert enrollment_audits.count() == audit_count

        data = self.command.process_enrollment_audit(enrollment)
        assert data == [{
            'enrolled_by': audit.enrolled_by.username,
            'enrolled_email': audit.enrolled_email,
            'time_stamp': audit.time_stamp,
            'state_transition': audit.state_transition,
            'reason': audit.reason,
            'role': audit.role,
        } for audit in enrollment_audits]

    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_enrollments', return_value=[])
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_course_overview', return_value={})
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_enrollment_allowed', return_value=[])
    @patch('openedx.core.djangoapps.appsembler.sites.management.commands.offboard.Command.process_access_roles', return_value=[])
    def test_process_courses(self, mock1, mock2, mock3, mock4):
        courses_count = 3
        organization = OrganizationFactory.create(name='test')

        query_set = OrganizationCourse.objects.filter(organization__in=[organization])
        assert query_set.count() == 0

        for i in range(courses_count):
            OrganizationCourseFactory(
                organization=organization,
                course_id=str(CourseFactory().id)
            )

        query_set = OrganizationCourse.objects.filter(organization__in=[organization])
        assert query_set.count() == courses_count

        data = self.command.process_courses(organization)
        assert data == [{
            'course_id': course.course_id,
            'active': course.active,
            'enrollments': [],
            'course_overview': {},
            'enrollment_allowed': [],
            'access_roles': [],
        } for course in query_set]

    @patch('django.core.files.File.write')
    def test_write_to_file(self, mock_write):
        path = '/dummy/path.json'
        content = '{"tetst": "contetnt"}'

        with patch("builtins.open", mock_open()) as mock_file:
            self.command.write_to_file(path, content)

        mock_file.assert_called_once_with(path, 'w')
        assert mock_write.called_with(content)

    @staticmethod
    def create_org_users(org, new_user_count):
        result = []
        for i in range(new_user_count):
            result.append(UserFactory())
            create_organization_mapping(user=result[i], organization=org)
        return result


class DisableCustomDomainCommandTestCase(TestCase):
    """
    Test ./manage.py lms disable_custom_domain mysite.example.com
    """
    def test_disable_custom_domain(self):
        disable_domain = "test-custom-domain.example.com"
        subdomain = "test-custom-domain.tahoe.appsembler.com"

        s = SiteFactory.create(domain=disable_domain)
        AlternativeDomainFactory.create(domain=subdomain, site=s)

        call_command('disable_custom_domain', disable_domain)

        # we expect the Site now has `subdomain`
        assert Site.objects.filter(domain=subdomain).exists()
        # and that the AlternativeDomain is gone
        assert not AlternativeDomain.objects.filter(domain=subdomain).exists()

        # there shouldn't be an AlternativeDomain for
        assert not AlternativeDomain.objects.filter(domain=disable_domain).exists()
        # and there shouldn't be a lingering/duplicate Site for the old one either
        assert not Site.objects.filter(domain=disable_domain).exists()
