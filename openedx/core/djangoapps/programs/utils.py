# -*- coding: utf-8 -*-
"""Helper functions for working with Programs."""
from collections import defaultdict
import datetime
from urlparse import urljoin

from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.functional import cached_property
from opaque_keys.edx.keys import CourseKey
from pytz import utc

from course_modes.models import CourseMode
from lms.djangoapps.certificates import api as certificate_api
from lms.djangoapps.commerce.utils import EcommerceService
from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.lib.edx_api_utils import get_edx_api_data
from student.models import CourseEnrollment
from util.date_utils import strftime_localized
from util.organizations_helpers import get_organization_by_short_name


# The datetime module's strftime() methods require a year >= 1900.
DEFAULT_ENROLLMENT_START_DATE = datetime.datetime(1900, 1, 1, tzinfo=utc)


def get_program_marketing_url(programs_config):
    """Build a URL to be used when linking to program details on a marketing site."""
    return urljoin(settings.MKTG_URLS.get('ROOT'), programs_config.marketing_path).rstrip('/')


def attach_program_detail_url(programs):
    """Extend program representations by attaching a URL to be used when linking to program details.

    Facilitates the building of context to be passed to templates containing program data.

    Arguments:
        programs (list): Containing dicts representing programs.

    Returns:
        list, containing extended program dicts
    """
    for program in programs:
        program['detail_url'] = reverse('program_details_view', kwargs={'program_uuid': program['uuid']})

    return programs


def munge_progress_map(progress_map):
    """
    Temporary utility for making progress maps look like they were built using
    data from the deprecated programs service.

    Clean up of this debt is tracked by ECOM-4418.
    """
    progress_map['id'] = progress_map.pop('uuid')

    return progress_map


class ProgramProgressMeter(object):
    """Utility for gauging a user's progress towards program completion.

    Arguments:
        user (User): The user for which to find programs.

    Keyword Arguments:
        enrollments (list): List of the user's enrollments.
    """
    def __init__(self, user, enrollments=None):
        self.user = user

        self.enrollments = enrollments or list(CourseEnrollment.enrollments_for_user(self.user))
        self.enrollments.sort(key=lambda e: e.created, reverse=True)

        # enrollment.course_id is really a CourseKey (╯ಠ_ಠ）╯︵ ┻━┻
        self.course_run_ids = [unicode(e.course_id) for e in self.enrollments]

        self.programs = attach_program_detail_url(get_programs())

    def invert_programs(self):
        """Intersect programs and enrollments.

        Builds a dictionary of program dict lists keyed by course run ID. The
        resulting dictionary is suitable in applications where programs must be
        filtered by the course runs they contain (e.g., the student dashboard).

        Returns:
            defaultdict, programs keyed by course run ID
        """
        inverted_programs = defaultdict(list)

        for program in self.programs:
            for course in program['courses']:
                for course_run in course['course_runs']:
                    course_run_id = course_run['key']
                    if course_run_id in self.course_run_ids:
                        program_list = inverted_programs[course_run_id]
                        if program not in program_list:
                            program_list.append(program)

        # Sort programs by title for consistent presentation.
        for program_list in inverted_programs.itervalues():
            program_list.sort(key=lambda p: p['title'])

        return inverted_programs

    @cached_property
    def engaged_programs(self):
        """Derive a list of programs in which the given user is engaged.

        Returns:
            list of program dicts, ordered by most recent enrollment
        """
        inverted_programs = self.invert_programs()

        programs = []
        # Remember that these course run ids are derived from a list of
        # enrollments sorted from most recent to least recent. Iterating
        # over the values in inverted_programs alone won't yield a program
        # ordering consistent with the user's enrollments.
        for course_run_id in self.course_run_ids:
            for program in inverted_programs[course_run_id]:
                # Dicts aren't a hashable type, so we can't use a set. Sets also
                # aren't ordered, which is important here.
                if program not in programs:
                    programs.append(program)

        return programs

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

            for course in program['courses']:
                # TODO: What are these titles used for? If they're not used by
                # the front-end, pass integer counts instead.
                title = course['title']

                if self._is_course_complete(course):
                    completed.append(title)
                elif self._is_course_in_progress(course):
                    in_progress.append(title)
                else:
                    not_started.append(title)

            progress.append({
                'uuid': program['uuid'],
                'completed': completed,
                'in_progress': in_progress,
                'not_started': not_started,
            })

        return progress

    @property
    def completed_programs(self):
        """Identify programs completed by the student.

        Returns:
            list of UUIDs, each identifying a completed program.
        """
        return [program['uuid'] for program in self.programs if self._is_program_complete(program)]

    def _is_program_complete(self, program):
        """Check if a user has completed a program.

        A program is completed if the user has completed all nested courses.

        Arguments:
            program (dict): Representing the program whose completion to assess.

        Returns:
            bool, indicating whether the program is complete.
        """
        return all(self._is_course_complete(course) for course in program['courses'])

    def _is_course_complete(self, course):
        """Check if a user has completed a course.

        A course is completed if the user has earned a certificate for any of
        the nested course runs.

        Arguments:
            course (dict): Containing nested course runs.

        Returns:
            bool, indicating whether the course is complete.
        """

        def reshape(course_run):
            """
            Modify the structure of a course run dict to facilitate comparison
            with course run certificates.
            """
            return {
                'course_run_id': course_run['key'],
                # A course run's type is assumed to indicate which mode must be
                # completed in order for the run to count towards program completion.
                # This supports the same flexible program construction allowed by the
                # old programs service (e.g., completion of an old honor-only run may
                # count towards completion of a course in a program). This may change
                # in the future to make use of the more rigid set of "applicable seat
                # types" associated with each program type in the catalog.
                'type': course_run['type'],
            }

        return any(reshape(course_run) in self.completed_course_runs for course_run in course['course_runs'])

    @property
    def completed_course_runs(self):
        """
        Determine which course runs have been completed by the user.

        Returns:
            list of dicts, each representing a course run certificate
        """
        course_run_certificates = certificate_api.get_certificates_for_user(self.user.username)
        return [
            {'course_run_id': unicode(certificate['course_key']), 'type': certificate['type']}
            for certificate in course_run_certificates
            if certificate_api.is_passing_status(certificate['status'])
        ]

    def _is_course_in_progress(self, course):
        """Check if a user is in the process of completing a course.

        A user is considered to be in the process of completing a course if
        they're enrolled in any of the nested course runs.

        Arguments:
            course (dict): Containing nested course runs.

        Returns:
            bool, indicating whether the course is in progress.
        """
        return any(course_run['key'] in self.course_run_ids for course_run in course['course_runs'])


# pylint: disable=missing-docstring
class ProgramDataExtender(object):
    """
    Utility for extending program course codes with CourseOverview and
    CourseEnrollment data.

    Arguments:
        program_data (dict): Representation of a program. Note that this dict must
            be formatted as if it was returned by the deprecated program service.
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
            user_id=self.user.id,  # Providing user_id allows us to fall back to PDF certificates
                                   # if web certificates are not configured for a given course.
            course_id=self.course_key,
            uuid=certificate_uuid,
        ) if certificate_uuid else None

    def _attach_run_mode_course_image_url(self, run_mode):
        run_mode['course_image_url'] = self.course_overview.course_image_url

    def _attach_run_mode_course_url(self, run_mode):
        run_mode['course_url'] = reverse('course_root', args=[self.course_key])

    def _attach_run_mode_end_date(self, run_mode):
        run_mode['end_date'] = self.course_overview.end

    def _attach_run_mode_enrollment_open_date(self, run_mode):
        run_mode['enrollment_open_date'] = strftime_localized(self.enrollment_start, 'SHORT_DATE')

    def _attach_run_mode_is_course_ended(self, run_mode):
        end_date = self.course_overview.end or datetime.datetime.max.replace(tzinfo=utc)
        run_mode['is_course_ended'] = end_date < datetime.datetime.now(utc)

    def _attach_run_mode_is_enrolled(self, run_mode):
        run_mode['is_enrolled'] = CourseEnrollment.is_enrolled(self.user, self.course_key)

    def _attach_run_mode_is_enrollment_open(self, run_mode):
        enrollment_end = self.course_overview.enrollment_end or datetime.datetime.max.replace(tzinfo=utc)
        run_mode['is_enrollment_open'] = self.enrollment_start <= datetime.datetime.now(utc) < enrollment_end

    def _attach_run_mode_start_date(self, run_mode):
        run_mode['start_date'] = self.course_overview.start

    def _attach_run_mode_advertised_start(self, run_mode):
        run_mode['advertised_start'] = self.course_overview.advertised_start

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
