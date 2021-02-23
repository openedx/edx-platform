"""Django management command to force certificate regeneration for one user"""


import copy
import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from opaque_keys.edx.keys import CourseKey
from six import text_type
from xmodule.modulestore.django import modulestore

from lms.djangoapps.badges.events.course_complete import get_completion_badge
from lms.djangoapps.badges.utils import badges_enabled
from lms.djangoapps.certificates.api import regenerate_user_certificates

LOGGER = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    """
    Management command to recreate the certificate for
    a given user in a given course.
    """

    help = """Put a request on the queue to recreate the certificate for a particular user in a particular course."""

    def add_arguments(self, parser):
        parser.add_argument('-n', '--noop',
                            action='store_true',
                            dest='noop',
                            help="Don't grade or add certificate requests to the queue")
        parser.add_argument('--insecure',
                            action='store_true',
                            dest='insecure',
                            help="Don't use https for the callback url to the LMS, useful in http test environments")
        parser.add_argument('-c', '--course',
                            metavar='COURSE_ID',
                            dest='course',
                            required=True,
                            help='The course id (e.g., mit/6-002x/circuits-and-electronics) for which the student '
                                 'named in <username> should be graded')
        parser.add_argument('-u', '--user',
                            metavar='USERNAME',
                            dest='username',
                            required=True,
                            help='The username or email address for whom grading and certification should be requested')
        parser.add_argument('-G', '--grade',
                            metavar='GRADE',
                            dest='grade_value',
                            default=None,
                            help='The grade string, such as "Distinction", which is passed to the certificate agent')
        parser.add_argument('-T', '--template',
                            metavar='TEMPLATE',
                            dest='template_file',
                            default=None,
                            help='The template file used to render this certificate, like "QMSE01-distinction.pdf"')

    def handle(self, *args, **options):

        # Scrub the username from the log message
        cleaned_options = copy.copy(options)
        if 'username' in cleaned_options:
            cleaned_options['username'] = '<USERNAME>'
        LOGGER.info(
            (
                u"Starting to create tasks to regenerate certificates "
                u"with arguments %s and options %s"
            ),
            text_type(args),
            text_type(cleaned_options)
        )

        # try to parse out the course from the serialized form
        course_id = CourseKey.from_string(options['course'])
        user = options['username']

        kwargs = (Q(username=user) | Q(email=user)), Q(courseenrollment__course_id=course_id)
        student = User.objects.filter(kwargs).first()
        if not student:
            raise CommandError("User {} does not exist.".format(user))

        course = modulestore().get_course(course_id, depth=2)

        if not options['noop']:
            LOGGER.info(
                (
                    u"Adding task to the XQueue to generate a certificate "
                    u"for student %s in course '%s'."
                ),
                student.id,
                course_id
            )

            if badges_enabled() and course.issue_badges:
                badge_class = get_completion_badge(course_id, student)
                badge = badge_class.get_for_user(student)

                if badge:
                    badge.delete()
                    LOGGER.info(u"Cleared badge for student %s.", student.id)

            # Add the certificate request to the queue
            regenerate_user_certificates(
                student, course_id, course=course,
                forced_grade=options['grade_value'],
                template_file=options['template_file'],
                insecure=options['insecure']
            )

            LOGGER.info(
                (
                    u"Added a certificate regeneration task to the XQueue "
                    u"for student %s in course '%s'."
                ),
                student.id,
                text_type(course_id)
            )

        else:
            LOGGER.info(
                (
                    u"Skipping certificate generation for "
                    u"student %s in course '%s' "
                    u"because the noop flag is set."
                ),
                student.id,
                text_type(course_id)
            )

        LOGGER.info(
            (
                u"Finished regenerating certificates command for "
                u"user %s and course '%s'."
            ),
            student.id,
            text_type(course_id)
        )
