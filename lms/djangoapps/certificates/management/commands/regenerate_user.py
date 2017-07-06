"""Django management command to force certificate regeneration for one user"""

import logging
import copy
from optparse import make_option
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from badges.events.course_complete import get_completion_badge
from xmodule.modulestore.django import modulestore
from certificates.api import regenerate_user_certificates

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to recreate the certificate for
    a given user in a given course.
    """

    help = """Put a request on the queue to recreate the certificate for a particular user in a particular course."""

    option_list = BaseCommand.option_list + (
        make_option('-n', '--noop',
                    action='store_true',
                    dest='noop',
                    default=False,
                    help="Don't grade or add certificate requests to the queue"),
        make_option('--insecure',
                    action='store_true',
                    dest='insecure',
                    default=False,
                    help="Don't use https for the callback url to the LMS, useful in http test environments"),
        make_option('-c', '--course',
                    metavar='COURSE_ID',
                    dest='course',
                    default=False,
                    help='The course id (e.g., mit/6-002x/circuits-and-electronics) for which the student named in'
                         '<username> should be graded'),
        make_option('-u', '--user',
                    metavar='USERNAME',
                    dest='username',
                    default=False,
                    help='The username or email address for whom grading and certification should be requested'),
        make_option('-G', '--grade',
                    metavar='GRADE',
                    dest='grade_value',
                    default=None,
                    help='The grade string, such as "Distinction", which should be passed to the certificate agent'),
        make_option('-T', '--template',
                    metavar='TEMPLATE',
                    dest='template_file',
                    default=None,
                    help='The template file used to render this certificate, like "QMSE01-distinction.pdf"'),
    )

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
            unicode(args),
            unicode(cleaned_options)
        )

        if options['course']:
            # try to parse out the course from the serialized form
            try:
                course_id = CourseKey.from_string(options['course'])
            except InvalidKeyError:
                LOGGER.warning(
                    (
                        u"Course id %s could not be parsed as a CourseKey; "
                        u"falling back to SlashSeparatedCourseKey.from_deprecated_string()"
                    ),
                    options['course']
                )
                course_id = SlashSeparatedCourseKey.from_deprecated_string(options['course'])
        else:
            raise CommandError("You must specify a course")

        user = options['username']
        if not (course_id and user):
            raise CommandError('both course id and student username are required')

        student = None
        if '@' in user:
            student = User.objects.get(email=user, courseenrollment__course_id=course_id)
        else:
            student = User.objects.get(username=user, courseenrollment__course_id=course_id)

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

            if course.issue_badges:
                badge_class = get_completion_badge(course_id, student)
                badge = badge_class.get_for_user(student)

                if badge:
                    badge.delete()
                    LOGGER.info(u"Cleared badge for student %s.", student.id)

            # Add the certificate request to the queue
            ret = regenerate_user_certificates(
                student, course_id, course=course,
                forced_grade=options['grade_value'],
                template_file=options['template_file'],
                insecure=options['insecure']
            )

            LOGGER.info(
                (
                    u"Added a certificate regeneration task to the XQueue "
                    u"for student %s in course '%s'. "
                    u"The new certificate status is '%s'."
                ),
                student.id,
                unicode(course_id),
                ret
            )

        else:
            LOGGER.info(
                (
                    u"Skipping certificate generation for "
                    u"student %s in course '%s' "
                    u"because the noop flag is set."
                ),
                student.id,
                unicode(course_id)
            )

        LOGGER.info(
            (
                u"Finished regenerating certificates command for "
                u"user %s and course '%s'."
            ),
            student.id,
            unicode(course_id)
        )
