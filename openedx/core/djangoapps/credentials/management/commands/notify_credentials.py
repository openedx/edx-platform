"""
A few places in the LMS want to notify the Credentials service when certain events
happen (like certificates being awarded or grades changing). To do this, they
listen for a signal. Sometimes we want to rebuild the data on these apps
regardless of an actual change in the database, either to recover from a bug or
to bootstrap a new feature we're rolling out for the first time.

This management command will manually trigger the receivers we care about.
(We don't want to trigger all receivers for these signals, since these are busy
signals.)
"""
from __future__ import print_function, division
import logging
import math
import time
import sys

import dateutil.parser
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from pytz import UTC

from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.grades.models import PersistentCourseGrade
from openedx.core.djangoapps.credentials.models import NotifyCredentialsConfig
from openedx.core.djangoapps.credentials.signals import handle_cert_change, send_grade_if_interesting
from openedx.core.djangoapps.programs.signals import handle_course_cert_changed
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


log = logging.getLogger(__name__)


def certstr(cert):
    return '{} for user {}'.format(cert.course_id, cert.user.username)


def gradestr(grade):
    return '{} for user {}'.format(grade.course_id, grade.user_id)


def parsetime(timestr):
    dt = dateutil.parser.parse(timestr)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def paged_query(queryset, delay, page_size):
    """
    A generator that iterates through a queryset but only resolves chunks of it at once, to avoid overwhelming memory
    with a giant query. Also adds an optional delay between yields, to help with load.
    """
    count = queryset.count()
    pages = int(math.ceil(count / page_size))

    for page in range(pages):
        page_start = page * page_size
        page_end = page_start + page_size
        subquery = queryset[page_start:page_end]

        if delay and page:
            time.sleep(delay)

        for i, item in enumerate(subquery, start=1):
            yield page_start + i, item


class Command(BaseCommand):
    """
    Example usage:

    # Process all certs/grades changes for a given course:
    $ ./manage.py lms --settings=devstack_docker notify_credentials \
    --courses course-v1:edX+DemoX+Demo_Course

    # Process all certs/grades changes in a given time range:
    $ ./manage.py lms --settings=devstack_docker notify_credentials \
    --start-date 2018-06-01 --end-date 2018-07-31

    A Dry Run will produce output that looks like:

        DRY-RUN: This command would have handled changes for...
        3 Certificates:
            course-v1:edX+RecordsSelfPaced+1 for user records_one_cert
            course-v1:edX+RecordsSelfPaced+1 for user records
            course-v1:edX+RecordsSelfPaced+1 for user records_unverified
        3 Grades:
            course-v1:edX+RecordsSelfPaced+1 for user 14
            course-v1:edX+RecordsSelfPaced+1 for user 17
            course-v1:edX+RecordsSelfPaced+1 for user 18
    """
    help = (
        u"Simulate certificate/grade changes without actually modifying database "
        u"content. Specifically, trigger the handlers that send data to Credentials."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Just show a preview of what would happen.',
        )
        parser.add_argument(
            '--site',
            default=None,
            help="Site domain to notify for (if not specified, all sites are notified). Uses course_org_filter.",
        )
        parser.add_argument(
            '--courses',
            nargs='+',
            help='Send information only for specific courses.',
        )
        parser.add_argument(
            '--start-date',
            type=parsetime,
            help='Send information only for certificates or grades that have changed since this date.',
        )
        parser.add_argument(
            '--end-date',
            type=parsetime,
            help='Send information only for certificates or grades that have changed before this date.',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0,
            help="Number of seconds to sleep between processing queries, so that we don't flood our queues.",
        )
        parser.add_argument(
            '--page-size',
            type=int,
            default=100,
            help="Number of items to query at once.",
        )
        parser.add_argument(
            '--args-from-database',
            action='store_true',
            help='Use arguments from the NotifyCredentialsConfig model instead of the command line.',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Run grade/cert change signal in verbose mode',
        )

    def get_args_from_database(self):
        """ Returns an options dictionary from the current NotifyCredentialsConfig model. """
        config = NotifyCredentialsConfig.current()
        if not config.enabled:
            raise CommandError('NotifyCredentialsConfig is disabled, but --args-from-database was requested.')

        # We don't need fancy shell-style whitespace/quote handling - none of our arguments are complicated
        argv = config.arguments.split()

        parser = self.create_parser('manage.py', 'notify_credentials')
        return parser.parse_args(argv).__dict__   # we want a dictionary, not a non-iterable Namespace object

    def handle(self, *args, **options):
        if options['args_from_database']:
            options = self.get_args_from_database()

        log.info(
            "notify_credentials starting, dry-run=%s, site=%s, delay=%d seconds",
            options['dry_run'],
            options['site'],
            options['delay']
        )

        cert_filter_args = {}
        grade_filter_args = {}

        try:
            site_config = SiteConfiguration.objects.get(site__domain=options['site']) if options['site'] else None
        except SiteConfiguration.DoesNotExist:
            log.error('No site configuration found for site %s', options['site'])

        if options['courses']:
            course_keys = self.get_course_keys(options['courses'])
            cert_filter_args['course_id__in'] = course_keys
            grade_filter_args['course_id__in'] = course_keys

        if options['start_date']:
            cert_filter_args['modified_date__gte'] = options['start_date']
            grade_filter_args['modified__gte'] = options['start_date']

        if options['end_date']:
            cert_filter_args['modified_date__lte'] = options['end_date']
            grade_filter_args['modified__lte'] = options['end_date']

        if not cert_filter_args:
            raise CommandError('You must specify a filter (e.g. --courses= or --start-date)')

        # pylint: disable=no-member
        certs = GeneratedCertificate.objects.filter(**cert_filter_args).order_by('modified_date')
        grades = PersistentCourseGrade.objects.filter(**grade_filter_args).order_by('modified')

        if options['dry_run']:
            self.print_dry_run(certs, grades)
        else:
            self.send_notifications(certs, grades,
                                    site_config=site_config,
                                    delay=options['delay'],
                                    page_size=options['page_size'],
                                    verbose=options['verbose'])

        log.info('notify_credentials finished')

    def send_notifications(self, certs, grades, site_config=None, delay=0, page_size=0, verbose=False):
        """ Run actual handler commands for the provided certs and grades. """

        # First, do certs
        for i, cert in paged_query(certs, delay, page_size):
            if site_config and not site_config.has_org(cert.course_id.org):
                log.info("Skipping credential changes %d for certificate %s", i, certstr(cert))
                continue

            log.info(
                "Handling credential changes %d for certificate %s",
                i, certstr(cert),
            )

            signal_args = {
                'sender': None,
                'user': cert.user,
                'course_key': cert.course_id,
                'mode': cert.mode,
                'status': cert.status,
                'verbose': verbose,
            }
            handle_course_cert_changed(**signal_args)
            handle_cert_change(**signal_args)

        # Then do grades
        for i, grade in paged_query(grades, delay, page_size):
            if site_config and not site_config.has_org(grade.course_id.org):
                log.info("Skipping grade changes %d for grade %s", i, gradestr(grade))
                continue

            log.info(
                "Handling grade changes %d for grade %s",
                i, gradestr(grade),
            )

            user = User.objects.get(id=grade.user_id)
            send_grade_if_interesting(
                user,
                grade.course_id,
                None,
                None,
                grade.letter_grade,
                grade.percent_grade,
                verbose=verbose
            )

    def get_course_keys(self, courses):
        """
        Return a list of CourseKeys that we will emit signals to.

        `courses` is an optional list of strings that can be parsed into
        CourseKeys. If `courses` is empty or None, we will default to returning
        all courses in the modulestore (which can be very expensive). If one of
        the strings passed in the list for `courses` does not parse correctly,
        it is a fatal error and will cause us to exit the entire process.
        """
        # Use specific courses if specified, but fall back to all courses.
        course_keys = []
        log.info("%d courses specified: %s", len(courses), ", ".join(courses))
        for course_id in courses:
            try:
                course_keys.append(CourseKey.from_string(course_id))
            except InvalidKeyError:
                log.fatal("%s is not a parseable CourseKey", course_id)
                sys.exit(1)

        return course_keys

    def print_dry_run(self, certs, grades):
        """Give a preview of what certs/grades we will handle."""
        print("DRY-RUN: This command would have handled changes for...")
        ITEMS_TO_SHOW = 10

        print(certs.count(), "Certificates:")
        for cert in certs[:ITEMS_TO_SHOW]:
            print("   ", certstr(cert))
        if certs.count() > ITEMS_TO_SHOW:
            print("    (+ {} more)".format(certs.count() - ITEMS_TO_SHOW))

        print(grades.count(), "Grades:")
        for grade in grades[:ITEMS_TO_SHOW]:
            print("   ", gradestr(grade))
        if grades.count() > ITEMS_TO_SHOW:
            print("    (+ {} more)".format(grades.count() - ITEMS_TO_SHOW))
