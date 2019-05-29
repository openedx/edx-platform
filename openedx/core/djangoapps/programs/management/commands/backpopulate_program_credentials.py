"""Management command for backpopulating missing program credentials."""
from __future__ import absolute_import

import logging
from collections import namedtuple
from functools import reduce  # pylint: disable=redefined-builtin

from django.contrib.sites.models import Site
from django.core.management import BaseCommand
from django.db.models import Q
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate
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
            logger.info(u'Enqueuing program certification tasks for %d candidates.', len(self.usernames))
        else:
            logger.info(
                u'Found %d candidates. To enqueue program certification tasks, pass the -c or --commit flags.',
                len(self.usernames)
            )
            return

        succeeded, failed = 0, 0
        for username in self.usernames:
            try:
                award_program_certificates.delay(username)
            except:  # pylint: disable=bare-except
                failed += 1
                logger.exception(u'Failed to enqueue task for user [%s]', username)
            else:
                succeeded += 1
                logger.debug(u'Successfully enqueued task for user [%s]', username)

        logger.info(
            u'Done. Successfully enqueued tasks for %d candidates. '
            u'Failed to enqueue tasks for %d candidates.',
            succeeded,
            failed
        )

    def _load_course_runs(self):
        """Find all course runs which are part of a program."""
        programs = []
        for site in Site.objects.all():
            logger.info(u'Loading programs from the catalog for site %s.', site.domain)
            programs.extend(get_programs(site))

        self.course_runs = self._flatten(programs)

    def _flatten(self, programs):
        """Flatten programs into a set of course runs."""
        course_runs = set()
        for program in programs:
            for course in program['courses']:
                for course_run in course['course_runs']:
                    key = CourseKey.from_string(course_run['key'])
                    course_runs.add(
                        CourseRun(key, course_run['type'])
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
            [Q(course_id=course_run.key, mode=course_run.type) for course_run in self.course_runs]
        )

        # Account for the fact that no-id-professional and professional are equivalent
        for course_run in self.course_runs:
            if course_run.type == CourseMode.PROFESSIONAL:
                course_run_query |= Q(course_id=course_run.key, mode=CourseMode.NO_ID_PROFESSIONAL_MODE)

        query = status_query & course_run_query

        username_dicts = GeneratedCertificate.eligible_available_certificates.filter(
            query
        ).values('user__username').distinct()
        self.usernames = [d['user__username'] for d in username_dicts]
