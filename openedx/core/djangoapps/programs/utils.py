# -*- coding: utf-8 -*-
"""Helper functions for working with Programs."""
from collections import defaultdict
from copy import deepcopy
import datetime
from urlparse import urljoin

from dateutil.parser import parse
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.utils.functional import cached_property
from opaque_keys.edx.keys import CourseKey
from pytz import utc
from itertools import chain

from course_modes.models import CourseMode
from lms.djangoapps.certificates import api as certificate_api
from lms.djangoapps.commerce.utils import EcommerceService
from lms.djangoapps.courseware.access import has_access
from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.credentials.utils import get_credentials
from student.models import CourseEnrollment
from util.date_utils import strftime_localized
from xmodule.modulestore.django import modulestore


# The datetime module's strftime() methods require a year >= 1900.
DEFAULT_ENROLLMENT_START_DATE = datetime.datetime(1900, 1, 1, tzinfo=utc)


def get_program_marketing_url(programs_config):
    """Build a URL used to link to programs on the marketing site."""
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


class ProgramProgressMeter(object):
    """Utility for gauging a user's progress towards program completion.

    Arguments:
        user (User): The user for which to find programs.

    Keyword Arguments:
        enrollments (list): List of the user's enrollments.
        uuid (str): UUID identifying a specific program. If provided, the meter
            will only inspect this one program, not all programs the user may be
            engaged with.
    """
    def __init__(self, user, enrollments=None, uuid=None):
        self.user = user

        self.enrollments = enrollments or list(CourseEnrollment.enrollments_for_user(self.user))
        self.enrollments.sort(key=lambda e: e.created, reverse=True)

        self.enrolled_run_modes = {}
        self.course_run_ids = []
        for enrollment in self.enrollments:
            # enrollment.course_id is really a CourseKey (╯ಠ_ಠ）╯︵ ┻━┻
            enrollment_id = unicode(enrollment.course_id)
            self.enrolled_run_modes[enrollment_id] = enrollment.mode
            # We can't use dict.keys() for this because the course run ids need to be ordered
            self.course_run_ids.append(enrollment_id)

        if uuid:
            self.programs = [get_programs(uuid=uuid)]
        else:
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

    def _is_course_in_progress(self, now, course):
        """Check if course qualifies as in progress as part of the program.

        A course is considered to be in progress if a user is enrolled in a run
        of the correct mode or a run of the correct mode is still available for enrollment.

        Arguments:
            now (datetime): datetime for now
            course (dict): Containing nested course runs.

        Returns:
            bool, indicating whether the course is in progress.
        """
        # Part 1: Check if any of the seats you are enrolled in qualify this course as in progress
        enrolled_runs = [run for run in course['course_runs'] if run['key'] in self.course_run_ids]
        # Check if the user is enrolled in the required mode for the run
        runs_with_required_mode = [
            run for run in enrolled_runs
            if run['type'] == self.enrolled_run_modes[run['key']]
        ]
        if runs_with_required_mode:
            # Check if the runs you are enrolled in with the right mode are not failed
            not_failed_runs = [run for run in runs_with_required_mode if run not in self.failed_course_runs]
            if not_failed_runs:
                return True
        # Part 2: Check if any of the seats you are not enrolled in
        # in the runs you are enrolled in qualify this course as in progress
        upgrade_deadlines = []
        for run in enrolled_runs:
            for seat in run['seats']:
                if seat['type'] == run['type'] and run['type'] != self.enrolled_run_modes[run['key']]:
                    upgrade_deadlines.append(seat['upgrade_deadline'])

        course_still_upgradeable = any(
            (deadline is not None) and (parse(deadline) > now) for deadline in upgrade_deadlines
        )
        return course_still_upgradeable

    def progress(self, programs=None, count_only=True):
        """Gauge a user's progress towards program completion.

        Keyword Arguments:
            programs (list): Specific list of programs to check the user's progress
                against. If left unspecified, self.engaged_programs will be used.

            count_only (bool): Whether or not to return counts of completed, in
                progress, and unstarted courses instead of serialized representations
                of the courses.

        Returns:
            list of dict, each containing information about a user's progress
                towards completing a program.
        """
        now = datetime.datetime.now(utc)

        progress = []
        programs = programs or self.engaged_programs
        for program in programs:
            program_copy = deepcopy(program)
            completed, in_progress, not_started = [], [], []

            for course in program_copy['courses']:
                if self._is_course_complete(course):
                    completed.append(course)
                elif self._is_course_enrolled(course):
                    course_in_progress = self._is_course_in_progress(now, course)
                    if course_in_progress:
                        in_progress.append(course)
                    else:
                        course['expired'] = not course_in_progress
                        not_started.append(course)
                else:
                    not_started.append(course)

            progress.append({
                'uuid': program_copy['uuid'],
                'completed': len(completed) if count_only else completed,
                'in_progress': len(in_progress) if count_only else in_progress,
                'not_started': len(not_started) if count_only else not_started,
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
            course_run_type = course_run['type']

            # Treat no-id-professional enrollments as professional
            if course_run_type == CourseMode.NO_ID_PROFESSIONAL_MODE:
                course_run_type = CourseMode.PROFESSIONAL

            return {
                'course_run_id': course_run['key'],
                # A course run's type is assumed to indicate which mode must be
                # completed in order for the run to count towards program completion.
                # This supports the same flexible program construction allowed by the
                # old programs service (e.g., completion of an old honor-only run may
                # count towards completion of a course in a program). This may change
                # in the future to make use of the more rigid set of "applicable seat
                # types" associated with each program type in the catalog.
                'type': course_run_type,
            }

        return any(reshape(course_run) in self.completed_course_runs for course_run in course['course_runs'])

    @cached_property
    def completed_course_runs(self):
        """
        Determine which course runs have been completed by the user.

        Returns:
            list of dicts, each representing a course run certificate
        """
        return self.course_runs_with_state['completed']

    @cached_property
    def failed_course_runs(self):
        """
        Determine which course runs have been failed by the user.

        Returns:
            list of dicts, each a course run ID
        """
        return [run['course_run_id'] for run in self.course_runs_with_state['failed']]

    @cached_property
    def course_runs_with_state(self):
        """
        Determine which course runs have been completed and failed by the user.

        Returns:
            dict with a list of completed and failed runs
        """
        course_run_certificates = certificate_api.get_certificates_for_user(self.user.username)
        completed_runs, failed_runs = [], []
        for certificate in course_run_certificates:
            course_data = {
                'course_run_id': unicode(certificate['course_key']),
                'type': certificate['type']
            }
            if certificate_api.is_passing_status(certificate['status']):
                completed_runs.append(course_data)
            else:
                failed_runs.append(course_data)
        return {'completed': completed_runs, 'failed': failed_runs}

    def _is_course_enrolled(self, course):
        """Check if a user is enrolled in a course.

        A user is considered to be enrolled in a course if
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
    Utility for extending program data meant for the program detail page with
    user-specific (e.g., CourseEnrollment) data.

    Arguments:
        program_data (dict): Representation of a program.
        user (User): The user whose enrollments to inspect.
    """
    def __init__(self, program_data, user):
        self.data = program_data
        self.user = user

        self.course_run_key = None
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

    def _extend_course_runs(self):
        """Execute course run data handlers."""
        for course in self.data['courses']:
            for course_run in course['course_runs']:
                # State to be shared across handlers.
                self.course_run_key = CourseKey.from_string(course_run['key'])
                self.course_overview = CourseOverview.get_from_id(self.course_run_key)
                self.enrollment_start = self.course_overview.enrollment_start or DEFAULT_ENROLLMENT_START_DATE

                self._execute('_attach_course_run', course_run)

    def _attach_course_run_certificate_url(self, run_mode):
        certificate_data = certificate_api.certificate_downloadable_status(self.user, self.course_run_key)
        certificate_uuid = certificate_data.get('uuid')
        run_mode['certificate_url'] = certificate_api.get_certificate_url(
            user_id=self.user.id,  # Providing user_id allows us to fall back to PDF certificates
                                   # if web certificates are not configured for a given course.
            course_id=self.course_run_key,
            uuid=certificate_uuid,
        ) if certificate_uuid else None

    def _attach_course_run_course_url(self, run_mode):
        run_mode['course_url'] = reverse('course_root', args=[self.course_run_key])

    def _attach_course_run_enrollment_open_date(self, run_mode):
        run_mode['enrollment_open_date'] = strftime_localized(self.enrollment_start, 'SHORT_DATE')

    def _attach_course_run_is_course_ended(self, run_mode):
        end_date = self.course_overview.end or datetime.datetime.max.replace(tzinfo=utc)
        run_mode['is_course_ended'] = end_date < datetime.datetime.now(utc)

    def _attach_course_run_is_enrolled(self, run_mode):
        run_mode['is_enrolled'] = CourseEnrollment.is_enrolled(self.user, self.course_run_key)

    def _attach_course_run_is_enrollment_open(self, run_mode):
        enrollment_end = self.course_overview.enrollment_end or datetime.datetime.max.replace(tzinfo=utc)
        run_mode['is_enrollment_open'] = self.enrollment_start <= datetime.datetime.now(utc) < enrollment_end

    def _attach_course_run_advertised_start(self, run_mode):
        """
        The advertised_start is text a course author can provide to be displayed
        instead of their course's start date. For example, if a course run were
        to start on December 1, 2016, the author might provide 'Winter 2016' as
        the advertised start.
        """
        run_mode['advertised_start'] = self.course_overview.advertised_start

    def _attach_course_run_upgrade_url(self, run_mode):
        required_mode_slug = run_mode['type']
        enrolled_mode_slug, _ = CourseEnrollment.enrollment_mode_for_user(self.user, self.course_run_key)
        is_mode_mismatch = required_mode_slug != enrolled_mode_slug
        is_upgrade_required = is_mode_mismatch and CourseEnrollment.is_enrolled(self.user, self.course_run_key)

        if is_upgrade_required:
            # Requires that the ecommerce service be in use.
            required_mode = CourseMode.mode_for_course(self.course_run_key, required_mode_slug)
            ecommerce = EcommerceService()
            sku = getattr(required_mode, 'sku', None)
            if ecommerce.is_enabled(self.user) and sku:
                run_mode['upgrade_url'] = ecommerce.checkout_page_url(required_mode.sku)
            else:
                run_mode['upgrade_url'] = None
        else:
            run_mode['upgrade_url'] = None


def get_certificates(user, extended_program):
    """
    Find certificates a user has earned related to a given program.

    Arguments:
        user (User): The user whose enrollments to inspect.
        extended_program (dict): The program for which to locate certificates.
            This is expected to be an "extended" program whose course runs already
            have certificate URLs attached.

    Returns:
        list: Contains dicts representing course run and program certificates the
            given user has earned which are associated with the given program.
    """
    certificates = []

    for course in extended_program['courses']:
        for course_run in course['course_runs']:
            url = course_run.get('certificate_url')
            if url:
                certificates.append({
                    'type': 'course',
                    'title': course_run['title'],
                    'url': url,
                })

                # We only want one certificate per course to be returned.
                break

    # A user can only have earned a program certificate if they've earned certificates
    # in associated course runs. If they haven't earned any course run certificates,
    # they can't have earned a program certificate, and we can save a network call
    # to the credentials service.
    if certificates:
        program_credentials = get_credentials(user, program_uuid=extended_program['uuid'])
        if program_credentials:
            certificates.append({
                'type': 'program',
                'title': extended_program['title'],
                'url': program_credentials[0]['certificate_url'],
            })

    return certificates


# pylint: disable=missing-docstring
class ProgramMarketingDataExtender(ProgramDataExtender):
    """
    Utility for extending program data meant for the program marketing page which lives in the
    edx-platform git repository with user-specific (e.g., CourseEnrollment) data, pricing data,
    and program instructor data.

    Arguments:
        program_data (dict): Representation of a program.
        user (User): The user whose enrollments to inspect.
    """
    def __init__(self, program_data, user):
        super(ProgramMarketingDataExtender, self).__init__(program_data, user)

        # Aggregate dict of instructors for the program keyed by name
        self.instructors = {}

        # Values for programs' price calculation.
        self.data['avg_price_per_course'] = 0
        self.data['number_of_courses'] = 0
        self.data['full_program_price'] = 0

    def _extend_program(self):
        """Aggregates data from the program data structure."""
        cache_key = 'program.instructors.{uuid}'.format(
            uuid=self.data['uuid']
        )
        program_instructors = cache.get(cache_key)

        for course in self.data['courses']:
            self._execute('_collect_course', course)
            if not program_instructors:
                for course_run in course['course_runs']:
                    self._execute('_collect_instructors', course_run)

        if not program_instructors:
            # We cache the program instructors list to avoid repeated modulestore queries
            program_instructors = self.instructors.values()
            cache.set(cache_key, program_instructors, 3600)

        self.data['instructors'] = program_instructors

    @classmethod
    def _handlers(cls, prefix):
        """Returns a generator yielding method names beginning with the given prefix."""
        # We use a set comprehension here to deduplicate the list of
        # function names given the fact that the subclass overrides
        # some functions on the parent class.
        return {name for name in chain(cls.__dict__, ProgramDataExtender.__dict__) if name.startswith(prefix)}

    def _attach_course_run_can_enroll(self, run_mode):
        run_mode['can_enroll'] = bool(has_access(self.user, 'enroll', self.course_overview))

    def _attach_course_run_certificate_url(self, run_mode):
        """
        We override this function here and stub it out because
        the superclass (ProgramDataExtender) requires a non-anonymous
        User which we may or may not have when rendering marketing
        pages. The certificate URL is not needed when rendering
        the program marketing page.
        """
        pass

    def _attach_course_run_upgrade_url(self, run_mode):
        if not self.user.is_anonymous():
            super(ProgramMarketingDataExtender, self)._attach_course_run_upgrade_url(run_mode)
        else:
            run_mode['upgrade_url'] = None

    def _collect_course_pricing(self, course):
        self.data['number_of_courses'] += 1
        course_runs = course['course_runs']
        if course_runs:
            seats = course_runs[0]['seats']
            if seats:
                self.data['full_program_price'] += float(seats[0]['price'])
            self.data['avg_price_per_course'] = self.data['full_program_price'] / self.data['number_of_courses']

    def _collect_instructors(self, course_run):
        """
        Extend the program data with instructor data. The instructor data added here is persisted
        on each course in modulestore and can be edited in Studio. Once the course metadata publisher tool
        supports the authoring of course instructor data, we will be able to migrate course
        instructor data into the catalog, retrieve it via the catalog API, and remove this code.
        """
        module_store = modulestore()
        course_run_key = CourseKey.from_string(course_run['key'])
        course_descriptor = module_store.get_course(course_run_key)
        if course_descriptor:
            course_instructors = getattr(course_descriptor, 'instructor_info', {})

            # Deduplicate program instructors using instructor name
            self.instructors.update(
                {instructor.get('name'): instructor for instructor in course_instructors.get('instructors', [])}
            )
