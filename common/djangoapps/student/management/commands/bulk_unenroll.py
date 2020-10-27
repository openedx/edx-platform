import logging

import unicodecsv
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from django.db.models import Q
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from student.models import CourseEnrollment, User


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Command(BaseCommand):

    help = """"
    Un-enroll bulk users from the courses.
    It expect that the data will be provided in a csv file format with
    first row being the header and columns will be as follows:
    user_id, username, email, course_id, is_verified, verification_date
    """

    def add_arguments(self, parser):
        parser.add_argument('-p', '--csv_path',
                            metavar='csv_path',
                            dest='csv_path',
                            required=True,
                            help='Path to CSV file.')

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        with open(csv_path) as csvfile:
            reader = unicodecsv.DictReader(csvfile)
            for row in reader:
                username = row['username']
                email = row['email']
                course_key = row['course_id']
                try:
                    user = User.objects.get(Q(username=username) | Q(email=email))
                except ObjectDoesNotExist:
                    user = None
                    msg = 'User with username {} or email {} does not exist'.format(username, email)
                    logger.warning(msg)

                try:
                    course_id = CourseKey.from_string(course_key)
                except InvalidKeyError:
                    course_id = None
                    msg = 'Invalid course id {course_id}, skipping un-enrollement for {username}, {email}'.format(**row)
                    logger.warning(msg)

                if user and course_id:
                    enrollment = CourseEnrollment.get_enrollment(user, course_id)
                    if not enrollment:
                        msg = 'Enrollment for the user {} in course {} does not exist!'.format(username, course_key)
                        logger.info(msg)
                    else:
                        try:
                            CourseEnrollment.unenroll(user, course_id, skip_refund=True)
                        except Exception as err:
                            msg = 'Error un-enrolling User {} from course {}: '.format(username, course_key, err)
                            logger.error(msg, exc_info=True)
