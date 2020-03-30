"""
Un-enroll Bulk users course wide as well as provided in csv
"""
import logging

import unicodecsv
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from student.models import CourseEnrollment, BulkUnenrollConfiguration

logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class Command(BaseCommand):
    """
    Management command to un-enroll course enrollments at once.
    """
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
        parser.add_argument('-c', '--course-id',
                            metavar='course_id',
                            dest='course-id',
                            required=False,
                            help='unenroll all users from provided course-id')

    def handle(self, *args, **options):

        csv_path = options['csv_path']
        course_id = options['course-id']

        if course_id:
            self.unenroll_all_users(course_id=course_id)
            return

        if csv_path:
            with open(csv_path, 'rb') as csv_file:
                self.unenroll_users_from_csv(csv_file)
        else:
            csv_file = BulkUnenrollConfiguration.current().csv_file
            self.unenroll_users_from_csv(csv_file)

    def unenroll_users_from_csv(self, csv_file):
        """
        Un-enroll the given set of users provided in csv
        """
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

            except Exception as err:  # pylint: disable=W0703
                msg = 'Error un-enrolling User {} from course {}: with error: {}'.format(username, course_key, err)
                logger.error(msg, exc_info=True)

        logger.info("Following users have been unenrolled successfully from the following courses: {users_unenrolled}"
                    .format(users_unenrolled=["{}:{}".format(k, v) for k, v in users_unenrolled.items()]))

    def unenroll_all_users(self, course_id):
        """
        Un-enroll all users from a given course
        """
        try:
            course_id = CourseKey.from_string(course_id)
        except InvalidKeyError:
            msg = 'Invalid course id {}, skipping un-enrollement.'.format(course_id)
            logger.warning(msg)
            return

        try:
            updated_count = CourseEnrollment.objects.filter(course_id=course_id, is_active=True).update(is_active=False)
            logger.info("{} users have been unenrolled successfully from the provided course: {}"
                        .format(updated_count, course_id))
        except Exception as err:  # pylint: disable=W0703
            msg = 'Error un-enrolling Users from course {}: with error: {}'.format(course_id, err)
            logger.error(msg, exc_info=True)
