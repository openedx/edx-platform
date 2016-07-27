# -*- coding: utf-8 -*-
"""Helper functions for working with Programs."""
import datetime
import logging

from django.core.urlresolvers import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.text import slugify
from opaque_keys.edx.keys import CourseKey
import pytz

from course_modes.models import CourseMode
from lms.djangoapps.certificates import api as certificate_api
from lms.djangoapps.commerce.utils import EcommerceService
from openedx.core.djangoapps.catalog.utils import get_run_marketing_url
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.lib.edx_api_utils import get_edx_api_data
from student.models import CourseEnrollment
from util.date_utils import strftime_localized
from util.organizations_helpers import get_organization_by_short_name


log = logging.getLogger(__name__)

# The datetime module's strftime() methods require a year >= 1900.
DEFAULT_ENROLLMENT_START_DATE = datetime.datetime(1900, 1, 1, tzinfo=pytz.UTC)


def get_programs(user, program_id=None):
    """Given a user, get programs from the Programs service.
    Returned value is cached depending on user permissions. Staff users making requests
    against Programs will receive unpublished programs, while regular users will only receive
    published programs.

    Arguments:
        user (User): The user to authenticate as when requesting programs.

    Keyword Arguments:
        program_id (int): Identifies a specific program for which to retrieve data.

    Returns:
        list of dict, representing programs returned by the Programs service.
    """
    programs_config = ProgramsApiConfig.current()

    # Bypass caching for staff users, who may be creating Programs and want
    # to see them displayed immediately.
    cache_key = programs_config.CACHE_KEY if programs_config.is_cache_enabled and not user.is_staff else None

    data = get_edx_api_data(programs_config, user, 'programs', resource_id=program_id, cache_key=cache_key)

    # TODO: Temporary, to be removed once category names are cased for display. ECOM-5018.
    if data and program_id:
        data['category'] = data['category'].lower()
    else:
        for program in data:
            program['category'] = program['category'].lower()

    return data


def flatten_programs(programs, course_ids):
    """Flatten the result returned by the Programs API.

    Arguments:
        programs (list): Serialized programs
        course_ids (list): Course IDs to key on.

    Returns:
        dict, programs keyed by course ID
    """
    flattened = {}

    for program in programs:
        try:
            for course_code in program['course_codes']:
                for run in course_code['run_modes']:
                    run_id = run['course_key']
                    if run_id in course_ids:
                        flattened.setdefault(run_id, []).append(program)
        except KeyError:
            log.exception('Unable to parse Programs API response: %r', program)

    return flattened


def get_programs_for_dashboard(user, course_keys):
    """Build a dictionary of programs, keyed by course.

    Given a user and an iterable of course keys, find all the programs relevant
    to the user's dashboard and return them in a dictionary keyed by course key.

    Arguments:
        user (User): The user to authenticate as when requesting programs.
        course_keys (list): List of course keys representing the courses in which
            the given user has active enrollments.

    Returns:
        dict, containing programs keyed by course. Empty if programs cannot be retrieved.
    """
    programs_config = ProgramsApiConfig.current()
    course_programs = {}

    if not programs_config.is_student_dashboard_enabled:
        log.debug('Display of programs on the student dashboard is disabled.')
        return course_programs

    programs = get_programs(user)
    if not programs:
        log.debug('No programs found for the user with ID %d.', user.id)
        return course_programs

    course_ids = [unicode(c) for c in course_keys]
    course_programs = flatten_programs(programs, course_ids)

    return course_programs


def get_programs_for_credentials(user, programs_credentials):
    """ Given a user and an iterable of credentials, get corresponding programs
    data and return it as a list of dictionaries.

    Arguments:
        user (User): The user to authenticate as for requesting programs.
        programs_credentials (list): List of credentials awarded to the user
            for completion of a program.

    Returns:
        list, containing programs dictionaries.
    """
    certificate_programs = []

    programs = get_programs(user)
    if not programs:
        log.debug('No programs for user %d.', user.id)
        return certificate_programs

    for program in programs:
        for credential in programs_credentials:
            if program['id'] == credential['credential']['program_id']:
                program['credential_url'] = credential['certificate_url']
                certificate_programs.append(program)

    return certificate_programs


def get_program_detail_url(program, marketing_root):
    """Construct the URL to be used when linking to program details.

    Arguments:
        program (dict): Representation of a program.
        marketing_root (str): Root URL used to build links to XSeries marketing pages.

    Returns:
        str, a link to program details
    """
    if ProgramsApiConfig.current().show_program_details:
        base = reverse('program_details_view', kwargs={'program_id': program['id']}).rstrip('/')
        slug = slugify(program['name'])
    else:
        base = marketing_root.rstrip('/')
        slug = program['marketing_slug']

    return '{base}/{slug}'.format(base=base, slug=slug)


def get_display_category(program):
    """ Given the program, return the category of the program for display
    Arguments:
        program (Program): The program to get the display category string from

    Returns:
        string, the category for display to the user.
        Empty string if the program has no category or is null.
    """
    display_candidate = ''
    if program and program.get('category'):
        if program.get('category') == 'xseries':
            display_candidate = 'XSeries'
        else:
            display_candidate = program.get('category', '').capitalize()
    return display_candidate


def get_completed_courses(student):
    """
    Determine which courses have been completed by the user.

    Args:
        student:
            User object representing the student

    Returns:
        iterable of dicts with structure {'course_id': course_key, 'mode': cert_type}

    """
    all_certs = certificate_api.get_certificates_for_user(student.username)
    return [
        {'course_id': unicode(cert['course_key']), 'mode': cert['type']}
        for cert in all_certs
        if certificate_api.is_passing_status(cert['status'])
    ]


class ProgramProgressMeter(object):
    """Utility for gauging a user's progress towards program completion.

    Arguments:
        user (User): The user for which to find programs.
    """
    def __init__(self, user):
        self.user = user
        self.course_ids = None

        self.programs = get_programs(self.user)
        self.course_certs = get_completed_courses(self.user)

    @cached_property
    def engaged_programs(self):
        """Derive a list of programs in which the given user is engaged.

        Returns:
            list of program dicts, ordered by most recent enrollment.
        """
        enrollments = CourseEnrollment.enrollments_for_user(self.user)
        enrollments = sorted(enrollments, key=lambda e: e.created, reverse=True)
        # enrollment.course_id is really a course key ಠ_ಠ
        self.course_ids = [unicode(e.course_id) for e in enrollments]

        flattened = flatten_programs(self.programs, self.course_ids)

        engaged_programs = []
        for course_id in self.course_ids:
            for program in flattened.get(course_id, []):
                if program not in engaged_programs:
                    engaged_programs.append(program)

        return engaged_programs

    @property
    def progress(self):
        """Gauge a user's progress towards program completion.

        Returns:
            list of dict, each containing information about a user's progress
                towards completing a program.
        """
        progress = []
        for program in self.engaged_programs:
            completed, in_progress, not_started = [], [], []

            for course_code in program['course_codes']:
                name = course_code['display_name']

                if self._is_course_code_complete(course_code):
                    completed.append(name)
                elif self._is_course_code_in_progress(course_code):
                    in_progress.append(name)
                else:
                    not_started.append(name)

            progress.append({
                'id': program['id'],
                'completed': completed,
                'in_progress': in_progress,
                'not_started': not_started,
            })

        return progress

    @property
    def completed_programs(self):
        """Identify programs completed by the student.

        Returns:
            list of int, each the ID of a completed program.
        """
        return [program['id'] for program in self.programs if self._is_program_complete(program)]

    def _is_program_complete(self, program):
        """Check if a user has completed a program.

        A program is completed if the user has completed all nested course codes.

        Arguments:
            program (dict): Representing the program whose completion to assess.

        Returns:
            bool, whether the program is complete.
        """
        return all(self._is_course_code_complete(course_code) for course_code in program['course_codes'])

    def _is_course_code_complete(self, course_code):
        """Check if a user has completed a course code.

        A course code is completed if the user has earned a certificate
        in the right mode for any nested run.

        Arguments:
            course_code (dict): Containing nested run modes.

        Returns:
            bool, whether the course code is complete.
        """
        return any(self._parse(run_mode) in self.course_certs for run_mode in course_code['run_modes'])

    def _is_course_code_in_progress(self, course_code):
        """Check if a user is in the process of completing a course code.

        A user is in the process of completing a course code if they're
        enrolled in the course.

        Arguments:
            course_code (dict): Containing nested run modes.

        Returns:
            bool, whether the course code is in progress.
        """
        return any(run_mode['course_key'] in self.course_ids for run_mode in course_code['run_modes'])

    def _parse(self, run_mode):
        """Modify the structure of a run mode dict.

        Arguments:
            run_mode (dict): With `course_key` and `mode_slug` keys.

        Returns:
            dict, with `course_id` and `mode` keys.
        """
        parsed = {
            'course_id': run_mode['course_key'],
            'mode': run_mode['mode_slug'],
        }

        return parsed


# pylint: disable=missing-docstring
class ProgramDataExtender(object):
    """Utility for extending program course codes with CourseOverview and CourseEnrollment data.

    Arguments:
        program_data (dict): Representation of a program.
        user (User): The user whose enrollments to inspect.
    """
    def __init__(self, program_data, user):
        self.data = program_data
        self.user = user
        self.course_key = None
        self.course_overview = None
        self.enrollment_start = None

    def extend(self):
        """Execute extension handlers, returning the extended data."""
        self._execute('_extend')
        return self.data

    def _execute(self, prefix, *args):
        """Call handlers whose name begins with the given prefix with the given arguments."""
        [getattr(self, handler)(*args) for handler in self._handlers(prefix)]  # pylint: disable=expression-not-assigned

    @classmethod
    def _handlers(cls, prefix):
        """Returns a generator yielding method names beginning with the given prefix."""
        return (name for name in cls.__dict__ if name.startswith(prefix))

    def _extend_organizations(self):
        """Execute organization data handlers."""
        for organization in self.data['organizations']:
            self._execute('_attach_organization', organization)

    def _extend_run_modes(self):
        """Execute run mode data handlers."""
        for course_code in self.data['course_codes']:
            for run_mode in course_code['run_modes']:
                # State to be shared across handlers.
                self.course_key = CourseKey.from_string(run_mode['course_key'])
                self.course_overview = CourseOverview.get_from_id(self.course_key)
                self.enrollment_start = self.course_overview.enrollment_start or DEFAULT_ENROLLMENT_START_DATE

                self._execute('_attach_run_mode', run_mode)

    def _attach_organization_logo(self, organization):
        # TODO: Cache the results of the get_organization_by_short_name call so
        # the database is hit less frequently.
        org_obj = get_organization_by_short_name(organization['key'])
        if org_obj and org_obj.get('logo'):
            organization['img'] = org_obj['logo'].url

    def _attach_run_mode_certificate_url(self, run_mode):
        certificate_data = certificate_api.certificate_downloadable_status(self.user, self.course_key)
        certificate_uuid = certificate_data.get('uuid')
        run_mode['certificate_url'] = certificate_api.get_certificate_url(
            course_id=self.course_key,
            uuid=certificate_uuid,
        ) if certificate_uuid else None

    def _attach_run_mode_course_image_url(self, run_mode):
        run_mode['course_image_url'] = self.course_overview.course_image_url

    def _attach_run_mode_course_url(self, run_mode):
        run_mode['course_url'] = reverse('course_root', args=[self.course_key])

    def _attach_run_mode_end_date(self, run_mode):
        run_mode['end_date'] = self.course_overview.end_datetime_text()

    def _attach_run_mode_enrollment_open_date(self, run_mode):
        run_mode['enrollment_open_date'] = strftime_localized(self.enrollment_start, 'SHORT_DATE')

    def _attach_run_mode_is_course_ended(self, run_mode):
        end_date = self.course_overview.end or datetime.datetime.max.replace(tzinfo=pytz.UTC)
        run_mode['is_course_ended'] = end_date < timezone.now()

    def _attach_run_mode_is_enrolled(self, run_mode):
        run_mode['is_enrolled'] = CourseEnrollment.is_enrolled(self.user, self.course_key)

    def _attach_run_mode_is_enrollment_open(self, run_mode):
        enrollment_end = self.course_overview.enrollment_end or datetime.datetime.max.replace(tzinfo=pytz.UTC)
        run_mode['is_enrollment_open'] = self.enrollment_start <= timezone.now() < enrollment_end

    def _attach_run_mode_marketing_url(self, run_mode):
        run_mode['marketing_url'] = get_run_marketing_url(self.course_key, self.user)

    def _attach_run_mode_start_date(self, run_mode):
        run_mode['start_date'] = self.course_overview.start_datetime_text()

    def _attach_run_mode_upgrade_url(self, run_mode):
        required_mode_slug = run_mode['mode_slug']
        enrolled_mode_slug, _ = CourseEnrollment.enrollment_mode_for_user(self.user, self.course_key)
        is_mode_mismatch = required_mode_slug != enrolled_mode_slug
        is_upgrade_required = is_mode_mismatch and CourseEnrollment.is_enrolled(self.user, self.course_key)

        if is_upgrade_required:
            # Requires that the ecommerce service be in use.
            required_mode = CourseMode.mode_for_course(self.course_key, required_mode_slug)
            ecommerce = EcommerceService()
            sku = getattr(required_mode, 'sku', None)

            if ecommerce.is_enabled(self.user) and sku:
                run_mode['upgrade_url'] = ecommerce.checkout_page_url(required_mode.sku)
            else:
                run_mode['upgrade_url'] = None
        else:
            run_mode['upgrade_url'] = None
