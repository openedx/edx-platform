"""
Management command which fixes ungraded certificates for students
"""


import logging

from django.core.management.base import BaseCommand

from lms.djangoapps.certificates.api import is_using_certificate_allowlist_and_is_on_allowlist
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.courseware import courses
from lms.djangoapps.grades.api import CourseGradeFactory

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to find and grade all students that need to be graded, unless the user is on the allowlist
    for that course run.
    """

    help = """
    Find all students that need to be graded
    and grade them.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-n',
            '--noop',
            action='store_true',
            dest='noop',
            default=False,
            help="Print but do not update the GeneratedCertificate table"
        )
        parser.add_argument(
            '-c',
            '--course',
            metavar='COURSE_ID',
            dest='course',
            default=False,
            help='Grade ungraded users for this course'
        )

    def handle(self, *args, **options):
        course_id = options['course']
        log.info('Fetching ungraded students for %s.', course_id)
        ungraded = GeneratedCertificate.objects.filter(
            course_id__exact=course_id
        ).filter(grade__exact='')
        course = courses.get_course_by_id(course_id)
        for cert in ungraded:
            if is_using_certificate_allowlist_and_is_on_allowlist(cert.user, course_id):
                log.info(f'{course_id} is using allowlist certificates, and the user {cert.user.id} is on its '
                         f'allowlist. Certificate will not be regraded')
            else:
                # grade the student
                grade = CourseGradeFactory().read(cert.user, course)
                log.info('grading %s - %s', cert.user, grade.percent)
                cert.grade = grade.percent
                if not options['noop']:
                    cert.save()
