"""
Management command which fixes ungraded certificates for students
"""


import logging

from django.core.management.base import BaseCommand

from lms.djangoapps.certificates.api import can_generate_certificate_task
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.courseware import courses
from lms.djangoapps.grades.api import CourseGradeFactory

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to find and grade all students that need to be graded, unless the course run is using V2 of
    course certificates.
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
            if can_generate_certificate_task(cert.user, course_id):
                log.info(f'{course_id} is using V2 certificates. Certificate will not be regraded for user '
                         f'{cert.user.id}.')
            else:
                # grade the student
                grade = CourseGradeFactory().read(cert.user, course)
                log.info('grading %s - %s', cert.user, grade.percent)
                cert.grade = grade.percent
                if not options['noop']:
                    cert.save()
