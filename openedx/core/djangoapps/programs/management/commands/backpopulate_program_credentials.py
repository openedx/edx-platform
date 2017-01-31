"""Management command for backpopulating missing program credentials."""
from collections import namedtuple
import logging

from django.contrib.auth.models import User
from django.core.management import BaseCommand
from django.db.models import Q
from opaque_keys.edx.keys import CourseKey

from certificates.models import GeneratedCertificate, CertificateStatuses  # pylint: disable=import-error
from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.programs.tasks.v1.tasks import award_program_certificates


# TODO: Log to console, even with debug mode disabled?
logger = logging.getLogger(__name__)  # pylint: disable=invalid-name
CourseRun = namedtuple('CourseRun', ['key', 'type'])


class Command(BaseCommand):
    """Management command for backpopulating missing program credentials.

    The command's goal is to pass a narrow subset of usernames to an idempotent
    Celery task for further (parallelized) processing.
    """
    help = 'Backpopulate missing program credentials.'
    course_runs = None
    usernames = None

    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--commit',
            action='store_true',
            dest='commit',
            default=False,
            help='Submit tasks for processing.'
        )

    def handle(self, *args, **options):
        logger.info('Loading programs from the catalog.')
        self._load_course_runs()

        logger.info('Looking for users who may be eligible for a program certificate.')
        self._load_usernames()

        if options.get('commit'):
            logger.info('Enqueuing program certification tasks for %d candidates.', len(self.usernames))
        else:
            logger.info(
                'Found %d candidates. To enqueue program certification tasks, pass the -c or --commit flags.',
                len(self.usernames)
            )
            return

        succeeded, failed = 0, 0
        for username in self.usernames:
            try:
                award_program_certificates.delay(username)
            except:  # pylint: disable=bare-except
                failed += 1
                logger.exception('Failed to enqueue task for user [%s]', username)
            else:
                succeeded += 1
                logger.debug('Successfully enqueued task for user [%s]', username)

        logger.info(
            'Done. Successfully enqueued tasks for %d candidates. '
            'Failed to enqueue tasks for %d candidates.',
            succeeded,
            failed
        )

    def _load_course_runs(self):
        """Find all course runs which are part of a program."""
        programs = get_programs()
        self.course_runs = self._flatten(programs)

    def _flatten(self, programs):
        """Flatten programs into a set of course runs."""
        course_runs = set()
        for program in programs:
            for course in program['courses']:
                for run in course['course_runs']:
                    key = CourseKey.from_string(run['key'])
                    course_runs.add(
                        CourseRun(key, run['type'])
                    )

        return course_runs

    def _load_usernames(self):
        """Identify a subset of users who may be eligible for a program certificate.

        This is done by finding users who have earned a qualifying certificate in
        at least one program course's course run.
        """
        status_query = Q(status__in=CertificateStatuses.PASSED_STATUSES)
        course_run_query = reduce(
            lambda x, y: x | y,
            # A course run's type is assumed to indicate which mode must be
            # completed in order for the run to count towards program completion.
            # This supports the same flexible program construction allowed by the
            # old programs service (e.g., completion of an old honor-only run may
            # count towards completion of a course in a program). This may change
            # in the future to make use of the more rigid set of "applicable seat
            # types" associated with each program type in the catalog.
            [Q(course_id=run.key, mode=run.type) for run in self.course_runs]
        )

        query = status_query & course_run_query

        username_dicts = GeneratedCertificate.eligible_certificates.filter(query).values('user__username').distinct()
        self.usernames = [d['user__username'] for d in username_dicts]
