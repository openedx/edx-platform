"""
Edly's management command to populate dummy data for provided sites on given date.
"""
from datetime import datetime, timedelta
import logging
from random import randint, sample

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError

from edly_panel_app.api.v1.constants import REGISTRATION_FIELDS_VALUES  # pylint: disable=no-name-in-module
from edly_panel_app.api.v1.helpers import _register_user  # pylint: disable=no-name-in-module
from edly_panel_app.models import EdlyUserActivity
from figures.models import SiteDailyMetrics, SiteMonthlyMetrics

from openedx.features.edly.models import EdlyUserProfile
from openedx.core.djangoapps.django_comment_common.models import assign_default_role
from openedx.core.djangoapps.django_comment_common.utils import seed_permissions_roles
from student.helpers import AccountValidationError
from student.roles import CourseInstructorRole, CourseStaffRole
from student import auth
from student.models import CourseAccessRole, CourseEnrollment
from util.organizations_helpers import add_organization_course, get_organization_by_short_name
from xmodule.course_module import CourseFields
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import DuplicateCourseError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Populate dummy data for given sites for provided date.
    """
    help = 'Populate panel sites data in edly insights for given list of sites.'

    def add_arguments(self, parser):
        """
        Add arguments for email list and date for reports.
        """
        parser.add_argument(
            '--sites',
            default='',
            help='Comma separated list of lms sites',
        )
        parser.add_argument(
            '--date',
            default=datetime.today().strftime('%m/%Y'),
            help='The month and year of the data to populate.'
        )

    def get_dummy_users(self, date_for):
        """
        Return random number of dummy users to register.
        """
        formatted_date = date_for.strftime('%m_%Y')
        dummy_users = []
        users_count = randint(10, 30)
        password = 'edx'
        user_prefix = 'dummy_user'
        REGISTRATION_FIELDS_VALUES.pop('username')
        REGISTRATION_FIELDS_VALUES.pop('name')
        REGISTRATION_FIELDS_VALUES.pop('password')
        REGISTRATION_FIELDS_VALUES.pop('email')
        REGISTRATION_FIELDS_VALUES.pop('confirm_email')
        for index in range(1, users_count):
            dummy_users.append(dict(
                username='{}_{}_{}'.format(user_prefix, index, formatted_date),
                email='{}_{}_{}@example.com'.format(user_prefix, index, formatted_date),
                name='{} {}_{}'.format(user_prefix, index, formatted_date),
                password=password,
                **REGISTRATION_FIELDS_VALUES,
            ))

        return dummy_users

    def get_dummy_courses(self, organization, populate_date):
        """
        Return random number of dummy courses to create.
        """
        course_name_prefix = 'Demo Course'
        course_count = randint(10, 20)
        courses = []
        month_for = populate_date.month
        year_for = populate_date.year
        for course in range(1, course_count):
            course_name = ('{} {} {}/{}').format(course_name_prefix, course, month_for, year_for)
            course_number = ('DC_{}_{}{}').format(course_count, month_for, year_for)
            course_run = '{}_{}'.format(month_for, year_for)
            courses.append(
                dict(
                    display_name=course_name,
                    number=course_number,
                    run=course_run,
                    org=organization,
                )
            )

        return courses

    def initialize_permissions(self, course_key, user_who_created_course):
        """
        Initializes a new course by enrolling the course creator as a student,
        and initializing Forum by seeding its permissions and assigning default roles.
        """
        seed_permissions_roles(course_key)
        CourseEnrollment.enroll(user_who_created_course, course_key)
        assign_default_role(course_key, user_who_created_course)

    def add_instructor(self, course_key, requesting_user, new_instructor):
        """
        Adds given user as instructor and staff to the given course,
        after verifying that the requesting_user has permission to do so.
        """
        CourseInstructorRole(course_key).add_users(new_instructor)
        auth.add_users(requesting_user, CourseStaffRole(course_key), new_instructor)

    def create_new_course_in_store(self, store, user, org, number, run, fields):
        """
        Creates the new course in module store.
        """
        fields.update({
            'language': getattr(settings, 'DEFAULT_COURSE_LANGUAGE', 'en'),
            'cert_html_view_enabled': True,
        })

        with modulestore().default_store(store):
            new_course = modulestore().create_course(
                org,
                number,
                run,
                user.id,
                fields=fields,
            )

        self.add_instructor(new_course.id, user, user)
        self.initialize_permissions(new_course.id, user)
        return new_course

    def create_new_course(self, user, org, number, run, fields):
        """
        Create a new course run.

        Raises:
            DuplicateCourseError: Course run already exists.
        """
        store_for_new_course = modulestore().default_modulestore.get_modulestore_type()
        new_course = self.create_new_course_in_store(store_for_new_course, user, org, number, run, fields)
        org_data = get_organization_by_short_name(org)
        add_organization_course(org_data, new_course.id)
        return new_course

    def get_dummy_metrics(self, date):
        """
        Returns random dates within month with dummy data.
        """
        start_date = date
        end_date = date + timedelta(days=30)
        number_of_dates = 15
        dummy_dates = [start_date]

        while start_date != end_date:
            start_date += timedelta(days=1)
            dummy_dates.append(start_date)

        dates = []
        dummy_dates = sample(dummy_dates, number_of_dates)
        for _date in dummy_dates:
            dates.append(dict(
                date_for=_date,
                todays_active_user_count=randint(10, 30),
                todays_active_learners_count=randint(10, 30),
                total_user_count=randint(10, 30),
                course_count=randint(10, 30),
                total_enrollment_count=randint(10, 30),
            ))

        return dates

    def register_dummy_users(self, site, dummy_users):
        """
        Registers dummy users for provided site.
        """
        extra_fields = site.configuration.get_value(
                'DJANGO_SETTINGS_OVERRIDE', {}
        ).get('REGISTRATION_EXTRA_FIELDS', {})

        for user in dummy_users:
            try:
                logger.info('Registering user: {}'.format(user['username']))
                _register_user(
                    params=user,
                    site=site,
                    site_configuration=dict(extra_fields=extra_fields),
                    message_context={},
                    tos_required=False,
                    skip_email=True,
                )
            except (AccountValidationError, ValidationError):
                logger.info('Failure registering user: {}'.format(user['username']))
                pass

    def create_dummy_courses(self, edx_org, courses, user):
        """
        Creates dummy courses in module store for given edx organization.
        """
        new_courses = []
        for course in courses:
            try:
                logger.info('Creating Dummy Course: {}'.format(course['run']))
                new_course = self.create_new_course(
                    user=user,
                    org=edx_org,
                    number=course.get('number'),
                    run=course.get('run'),
                    fields=dict(
                        display_name=course.get('display_name'),
                        wiki_slug=u"{0}.{1}.{2}".format(edx_org, course.get('number'), course.get('run'),),
                        start=CourseFields.start.default,
                    )
                )
                new_courses.append(new_course)
            except DuplicateCourseError:
                pass

        return new_courses

    def add_dummy_edly_activities(self, users, edly_sub_orgs, date):
        """
        Add users to edly sub organization and creates user activities.
        """
        edly_user_profiles = EdlyUserProfile.objects.filter(user__in=users)
        for user_profile in edly_user_profiles:
            logger.info('Saving edly user activity')
            user_profile.edly_sub_organizations.add(*edly_sub_orgs)
            user_profile.save()
            for edly_sub_org in edly_sub_orgs:
                try:
                    EdlyUserActivity.objects.get_or_create(
                        user=user_profile.user,
                        activity_date=date,
                        edly_sub_organization=edly_sub_org,
                    )
                except Exception:  # pylint: disable=broad-except
                    logger.exception('Unable to add edly_user_activity')

    def enroll_dummy_users_in_courses(self, courses, users):
        """
        Enrolls users in courses.
        """
        for course in courses:
            for user in users:
                logger.info('Enrolling user {} in course {}'.format(user.username, course.id))
                CourseEnrollment.enroll(user, course.id)

    def create_staff_users(self, org, users):
        indices = list(range(len(users)))
        indices = sample(indices, 5)
        for index in indices:
            CourseAccessRole.objects.get_or_create(
                user=users[index],
                org=org,
                role='global_course_creator',
            )

    def handle(self, *args, **options):
        """
        Command to populate panel site data for provided sites and date.
        """
        logger.info('Populating sites data.')
        sites_list = options['sites'].split(',')
        date_string = options['date']
        try:
            populate_date = datetime.strptime(date_string, '%m/%Y')
        except ValueError:
            raise CommandError(
                'The provided input date {} format is invalid. Please provide date in the format mm/yyyy'.format(
                    date_string,
                )
            )

        sites = Site.objects.filter(domain__in=sites_list)
        dates = self.get_dummy_metrics(populate_date)
        dummy_users = self.get_dummy_users(populate_date)
        sdm = SiteDailyMetrics.objects.filter()

        edly_sub_orgs = []
        for site in sites:
            edly_sub_org = getattr(site, 'edly_sub_org_for_lms', None)
            if not edly_sub_org:
                continue

            edly_sub_orgs.append(edly_sub_org)
            self.register_dummy_users(site, dummy_users)

            logger.info('Saving Site Monthly Metrics')
            smm, _ = SiteMonthlyMetrics.objects.get_or_create(
                month_for=populate_date,
                site=site,
                defaults=dict(active_user_count=randint(10, 30)),
            )
            smm.save()

            for date in dates:
                logger.info('Saving Site Daily Metrics')
                sdm, _ = SiteDailyMetrics.objects.get_or_create(
                    date_for=date['date_for'],
                    site_id=site.id,
                    defaults=date,
                )
                sdm.save()

        edx_organizations = []
        for edly_sub_org in edly_sub_orgs:
            edx_orgs = edly_sub_org.edx_organizations.all().values()
            edx_organizations.extend([org['short_name']for org in edx_orgs])

        user_objects = get_user_model().objects.filter(username__in=[user['username']for user in dummy_users])
        self.add_dummy_edly_activities(user_objects, edly_sub_orgs, populate_date)

        new_courses = []
        for edx_org in edx_organizations:
            courses = self.get_dummy_courses(edx_org, populate_date)
            new_courses.extend(self.create_dummy_courses(edx_org, courses, user_objects[0]))

        self.enroll_dummy_users_in_courses(new_courses, user_objects)
        edx_org = edx_organizations[0] if edx_organizations else 'edly'
        self.create_staff_users(edx_org, user_objects)

        logger.info('All sites data has been populated.')
