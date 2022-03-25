from datetime import datetime
import json
import os
import pkg_resources
import socket

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import ForeignKey
from tahoe_sites.api import get_organization_by_site

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration, SiteConfigurationHistory
from student.models import (
    CourseAccessRole,
    CourseEnrollment,
    CourseEnrollmentAllowed,
    ManualEnrollmentAudit,
    UserSignupSource,
    LanguageProficiency,
    SocialLink,
    UserAttribute,
    UserStanding,
    UserTestGroup,
)

from organizations.models import Organization, OrganizationCourse
from tahoe_sites.api import get_users_of_organization


class Command(BaseCommand):
    """
    Export a Tahoe website for customer offboarding.
    """
    def __init__(self, *args, **kwargs):
        self.debug = False
        self.default_path = os.getcwd()

        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument(
            'domain',
            help='The domain of the organization to be deleted.',
            type=str,
        )
        parser.add_argument(
            '-o', '--output',
            help='The location you want to direct your output to.',
            default=self.default_path,
            type=str,
        )
        parser.add_argument(
            '-d', '--debug',
            action='store_true',
            default=settings.DEBUG,
            help='Execute in debug mode (Will not commit or save changes).'
        )

    def handle(self, *args, **options):
        """
        Verifies the input and packs the site objects.
        """
        self.debug = options['debug']
        domain = options['domain']

        self.stdout.write('Inspecting project for potential problems...')
        self.check(display_num_errors=True)

        self.stdout.write(self.style.MIGRATE_HEADING('Offboarding "%s" in progress...' % domain))
        site = self.get_site(domain)

        export_data = {
            'date': datetime.now(),
            'site_domain': site.name,
            'objects': self.generate_objects(site),
        }

        output = json.dumps(
            export_data,
            sort_keys=True,
            indent=1,
            cls=DjangoJSONEncoder
        )

        self.debug_message('\nCommand output >>>')
        self.debug_message(self.style.SQL_KEYWORD(output))

        path = self.generate_file_path(site, options['output'])
        self.write_to_file(path, output)

        self.stdout.write(self.style.SUCCESS('\nSuccessfully offboarded "%s" site' % site.domain))

    def get_site(self, domain):
        """
        Locates the site to be offboarded and return its instance.

        :param domain: The domain of the ite to be returned.
        :return: Returns the site object.
        """
        self.debug_message('Exctracting the site object for {} ...'.format(domain))

        try:
            return Site.objects.get(domain=domain)
        except Site.DoesNotExist:
            raise CommandError('Cannot find a site for the provided domain "%s"!' % domain)

    def generate_objects(self, site):
        """
        Takes care of generating site objects.
        """
        self.debug_message('Generating site:%s objects...' % site.name)
        organization = get_organization_by_site(site=site)
        objects = {
            'site': self.process_site(site),
            'organizations': [
                self.process_organization(org) for org in [organization]
            ],
            'courses': self.process_courses(organization),
            'configurations': self.process_site_configurations(site),
            'configurations_history': self.process_site_configurations_history(site),
            'users': self.process_users(site),
        }

        return objects

    def process_courses(self, organization):
        """
        Processes site courses.
        """
        query_set = OrganizationCourse.objects.filter(organization=organization)
        self.debug_message('Processing organizations courses (%d total)...' % query_set.count())

        courses = []
        for course in query_set:
            self.stdout.write('Processing {} course data...'.format(course.course_id))
            course_id = CourseKey.from_string(course.course_id)
            course_overview = CourseOverview.get_from_id(course_id)

            courses.append({
                'course_id': course.course_id,
                'active': course.active,
                'enrollments': self.process_enrollments(course_overview, course_id=course_id),
                'course_overview': self.process_course_overview(course_overview, course_id=course_id),
                'enrollment_allowed': self.process_enrollment_allowed(course_id),
                'access_roles': self.process_access_roles(course_id),
            })

        return courses

    def process_users(self, site):
        """
        Processes site users.
        """
        signup_source_qs = UserSignupSource.objects.filter(site=site)

        self.debug_message('Processing {} site users ({} total)...'.format(
            site.name, signup_source_qs.count()))

        return [{
            'user_name': source.user.username,
            'first_name': source.user.first_name,
            'last_name': source.user.last_name,
            'active': source.user.is_active,
            'last_login': source.user.last_login,
            'permissions': [permission for permission in source.user.user_permissions.all()],
            'date_joined': source.user.date_joined,
            'profile': self.process_user_profile(source.user),
            'standing': self.process_user_standing(source.user),
            'test_groups': self.process_user_test_groups(source.user),
            'languages': self.process_user_languages(source.user),
            'social_links': self.process_social_links(source.user),
            'attributes': self.process_attributes(source.user),
        } for source in signup_source_qs]

    def process_access_roles(self, course_id):
        """
        Processes access roles for a given course.
        """
        access_roles_qs = CourseAccessRole.objects.filter(course_id=course_id)

        self.debug_message('Processing {} access roles ({} total)...'.format(
            course_id, access_roles_qs.count()))

        return [{
            'user': role.user.username,
            'org': role.org,
            'role': role.role,
        } for role in access_roles_qs]

    def process_enrollment_allowed(self, course_id):
        """
        Processes allowed enrollments for a given course ID.
        """
        enrollment_allowed_qs = CourseEnrollmentAllowed.objects.filter(course_id=course_id)
        self.debug_message('Processing {} allowed enrollments ({} total)...'.format(
            course_id, enrollment_allowed_qs.count()))

        return [{
            'email': record.email,
            'auto_enroll': record.auto_enroll,
            'user': record.user.username if record.user else None,
            'created': record.created,
        } for record in enrollment_allowed_qs]

    def process_attributes(self, user):
        """
        Processes user specific attributes.
        """
        user_attributes_qs = UserAttribute.objects.filter(user=user)
        self.debug_message('Processing {} user attributes ({} total)...'.format(user.username, user_attributes_qs.count()))

        return [{
            'name': attribute.name,
            'value': attribute.value,
        } for attribute in user_attributes_qs]

    def process_social_links(self, user):
        """
        Processes user social links.
        """
        social_links_qs = SocialLink.objects.filter(user_profile=user.profile)
        self.stdout.write('Processing {} user social links ({} total)...'.format(
            user.username, social_links_qs.count()))

        return [{
            'platform': link.platform,
            'social_link': link.social_link,
        } for link in social_links_qs]

    def process_user_languages(self, user):
        """
        Processes user's language proficiency.
        """
        languages_qs = LanguageProficiency.objects.filter(user_profile=user.profile)
        self.debug_message('Processing {} user social languages ({} total)...'.format(user.username, languages_qs.count()))
        return [language.code for language in languages_qs]

    def process_user_test_groups(self, user):
        """
        Processes user test groups.
        """
        test_groups_qs = UserTestGroup.objects.filter(users__id=user.id)
        self.debug_message('Processing {} user test groups...'.format(user.username, test_groups_qs.count()))

        return [{
            'name': test_group.name,
            'description': test_group.description,
        } for test_group in test_groups_qs]

    def process_user_standing(self, user):
        """
        Processes user standing.
        """
        self.debug_message('Processing {} user standing...'.format(user.username))

        try:
            standing = UserStanding.objects.get(user=user)
        except UserStanding.DoesNotExist:
            return {}

        return {
            'account_status': standing.account_status,
            'changed_by': standing.changed_by.username,
            'standing_last_changed_at': standing.standing_last_changed_at,
        }

    def process_user_profile(self, user):
        """
        Processes user profile.
        """
        self.debug_message('Processing {} user profile...'.format(user.username))
        profile = user.profile

        return {
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

    def process_enrollments(self, course_overview, course_id=''):
        """
        Processes course enrollments.
        """
        enrollments = CourseEnrollment.objects.filter(course=course_overview)
        self.debug_message('Processing {} course enrollments ({} total)...'.format(
            course_id, enrollments.count()))

        records = []
        for enrollment in enrollments:
            records.append({
                'user': enrollment.user.username,
                'created': enrollment.created,
                'active': enrollment.is_active,
                'mode': enrollment.mode,
                'audit': self.process_enrollment_audit(enrollment)
            })

        return records

    def process_enrollment_audit(self, enrollment):
        """
        Processes enrollment audit in MySQL db.
        """
        enrollment_audits = ManualEnrollmentAudit.objects.filter(enrollment=enrollment)

        self.stdout.write('Processing {} enrollment audit ({} total)...'.format(
            enrollment.user.username, enrollment_audits.count()))

        return [{
            'enrolled_by': audit.enrolled_by.username,
            'enrolled_email': audit.enrolled_email,
            'time_stamp': audit.time_stamp,
            'state_transition': audit.state_transition,
            'reason': audit.reason,
            'role': audit.role,
        } for audit in enrollment_audits]

    def process_course_overview(self, course_overview, course_id=''):
        """
        Processes a course overview object.
        """
        self.debug_message('Processing {} course overview...'.format(course_id))
        if not course_overview:
            return {}

        return {
            'version': course_overview.version,
            'org': course_overview.org,
            'display_name': course_overview.display_name,
            'display_number_with_default': course_overview.display_number_with_default,
            'display_org_with_default': course_overview.display_org_with_default,

            # Start/end dates
            'start': course_overview.start,
            'end': course_overview.end,
            'advertised_start': course_overview.advertised_start,
            'announcement': course_overview.announcement,

            # URLs
            'course_image_url': course_overview.course_image_url,
            'social_sharing_url': course_overview.social_sharing_url,
            'end_of_course_survey_url': course_overview.end_of_course_survey_url,

            # Certification data
            'certificates_display_behavior': course_overview.certificates_display_behavior,
            'certificates_show_before_end': course_overview.certificates_show_before_end,
            'cert_html_view_enabled': course_overview.cert_html_view_enabled,
            'has_any_active_web_certificate': course_overview.has_any_active_web_certificate,
            'cert_name_short': course_overview.cert_name_short,
            'cert_name_long': course_overview.cert_name_long,
            'certificate_available_date': course_overview.certificate_available_date,

            # Grading
            'lowest_passing_grade': course_overview.lowest_passing_grade,

            # Access parameters
            'days_early_for_beta': course_overview.days_early_for_beta,
            'mobile_available': course_overview.mobile_available,
            'visible_to_staff_only': course_overview.visible_to_staff_only,
            'pre_requisite_courses_json': course_overview._pre_requisite_courses_json,

            # Enrollment details
            'enrollment_start': course_overview.enrollment_start,
            'enrollment_end': course_overview.enrollment_end,
            'enrollment_domain': course_overview.enrollment_domain,
            'invitation_only': course_overview.invitation_only,
            'max_student_enrollments_allowed': course_overview.max_student_enrollments_allowed,

            # Catalog information
            'catalog_visibility': course_overview.catalog_visibility,
            'short_description': course_overview.short_description,
            'course_video_url': course_overview.course_video_url,
            'effort': course_overview.effort,
            'self_paced': course_overview.self_paced,
            'marketing_url': course_overview.marketing_url,
            'eligible_for_financial_aid': course_overview.eligible_for_financial_aid,
            'language': course_overview.language,
        }

    def process_site(self, site):
        self.stdout.write('Processing {} site...'.format(site.name))
        return {
            'name': site.name,
            'domain': site.domain,
        }

    def process_organization(self, organization):
        """
        Processes a given organization's data.
        """
        self.debug_message('Processing {} organization data...'.format(organization.name))
        return {
            'name': organization.name,
            'short_name': organization.short_name,
            'description': organization.description,
            'logo': organization.logo.url if organization.logo else '',
            'active': organization.active,
            'UUID': organization.edx_uuid,
            'created': organization.created,
            'users': self.process_organization_users(organization)
        }

    def process_organization_users(self, organization):
        """
        Processes a given organization's users.
        """
        self.debug_message('Processing {} organization users...'.format(organization.name))
        return [{
            'username': user.username,
            'active': user.is_active,
        } for user in get_users_of_organization(organization=organization).all()]

    def process_site_configurations(self, site):
        """
        Processes a given site's configurations
        """
        self.debug_message('Processing {} site configurations...'.format(site.name))

        try:
            site_configs = SiteConfiguration.objects.get(site=site)
        except Site.DoesNotExist:
            self.stdout.write('Cannot find %s site configs' % site.domain)
            return {}

        return {
            'enabled': site_configs.enabled,
            'values': site_configs.site_values,
            'sass_variables': site_configs.sass_variables,
            'page_elements': site_configs.page_elements,
        }

    def process_site_configurations_history(self, site):
        """
        Process configurations history for a given site.
        """
        self.debug_message('Processing %s site configurations history...' % site.name)

        return [
            {
                'enabled': record.enabled,
                'values': record.site_values,
            } for record in SiteConfigurationHistory.objects.filter(site=site)
        ]

    def generate_file_path(self, site, output):
        """
        Determines and returns the output file name.
        If the user specified a full path, then just return it. If a partial path
        has been specified, we add the file name to it and return. Other wise, we
        combine our base path with the file name and return them.
        """
        base = output or self.default_path

        if base.endswith('.json'):
            self.debug_message('Using the user\'s output path: %s' % output)
            return base

        now = datetime.now()
        timestamp = (now - datetime(1970, 1, 1)).total_seconds()

        self.debug_message('Generating file name and path...')
        file_name = '{}_{}.json'.format(site.name, timestamp)
        path = os.path.join(base, file_name)

        self.debug_message('Generated output location:%s' % path)
        return path

    def write_to_file(self, path, content):
        """
        Writes content in the specified path.
        """
        with open(path, 'w') as file:
            file.write(content)

        self.stdout.write(self.style.SQL_KEYWORD('\nExported objects saved in %s' % path))

    def debug_message(self, message):
        """
        Helps simplifying the process of printing debug message
        """
        if self.debug:
            self.stdout.write(message)
