"""
Management command which fixes ungraded certificates for students
"""


from certificates.models import GeneratedCertificate
from courseware import grades, courses
from django.test.client import RequestFactory
from django.core.management.base import BaseCommand
from optparse import make_option


class Command(BaseCommand):
    """
    Management command to find and grade all students that need to be graded.
    """

    help = """
    Find all students that need to be graded
    and grade them.
    """

    option_list = BaseCommand.option_list + (
        make_option(
            '-n',
            '--noop',
            action='store_true',
            dest='noop',
            default=False,
            help="Print but do not update the GeneratedCertificate table"
        ),
        make_option(
            '-c',
            '--course',
            metavar='COURSE_ID',
            dest='course',
            default=False,
            help='Grade ungraded users for this course'
        ),
    )

    def handle(self, *args, **options):
        course_id = options['course']
        print "Fetching ungraded students for {0}".format(course_id)
        ungraded = GeneratedCertificate.objects.filter(  # pylint: disable=no-member
            course_id__exact=course_id
        ).filter(grade__exact='')
        course = courses.get_course_by_id(course_id)
        factory = RequestFactory()
        request = factory.get('/')

        for cert in ungraded:
            # grade the student
            grade = grades.grade(cert.user, course)
            print "grading {0} - {1}".format(cert.user, grade['percent'])
            cert.grade = grade['percent']
            if not options['noop']:
                cert.save()
