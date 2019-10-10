from __future__ import absolute_import

import logging

import unicodecsv
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment, User, BulkUnenrollConfiguration

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
                            required=False,
                            help='Path to CSV file.')

    def handle(self, *args, **options):

        csv_path = options['csv_path']
        if csv_path:
            with open(csv_path, 'rb') as csv_file:
                self.unenroll_users(csv_file)
        else:
            csv_file = BulkUnenrollConfiguration.current().csv_file
            self.unenroll_users(csv_file)

    def unenroll_users(self, csv_file):
        reader = list(unicodecsv.DictReader(csv_file))
        users_unenrolled = {}
        for row in reader:
            username = row['username']
            course_key = row['course_id']

            try:
                course_id = CourseKey.from_string(row['course_id'])
            except InvalidKeyError:
                msg = 'Invalid course id {course_id}, skipping un-enrollement for {username}, {email}'.format(**row)
                logger.warning(msg)
                continue

            try:
                enrollment = CourseEnrollment.objects.get(user__username=username, course_id=course_id)
                enrollment.update_enrollment(is_active=False, skip_refund=True)
                if username in users_unenrolled:
                    users_unenrolled[username].append(course_key.encode())
                else:
                    users_unenrolled[username] = [course_key.encode()]

            except ObjectDoesNotExist:
                msg = 'Enrollment for the user {} in course {} does not exist!'.format(username, course_key)
                logger.info(msg)

            except Exception as err:
                msg = 'Error un-enrolling User {} from course {}: '.format(username, course_key, err)
                logger.error(msg, exc_info=True)

        logger.info("Following users have been unenrolled successfully from the following courses: {users_unenrolled}"
                    .format(users_unenrolled=["{}:{}".format(k, v) for k, v in users_unenrolled.items()]))
