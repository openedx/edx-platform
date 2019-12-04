"""
Management command to change many user enrollments in many courses using
csv file.
"""
from __future__ import absolute_import

import csv
import logging
from os import path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from student.models import CourseEnrollment, CourseEnrollmentAttribute, User

logger = logging.getLogger('student.management.commands.bulk_change_enrollment_csv')


class Command(BaseCommand):
    """
        Management command to change many user enrollments in many
        courses using the csv file
    """

    help = """
        Change the enrollment status of all the users specified in
        the csv file in the specified course to specified course
        mode.
        Could be used to update effected users by order
        placement issues. If large number of students are effected
        in different courses.
        Similar to bulk_change_enrollment but uses the csv file
        input format and can enroll students in multiple courses.

        Example:
            $ ... bulk_change_enrollment_csv csv_file_path
        """

    def add_arguments(self, parser):
        """ Add argument to the command parser. """
        parser.add_argument(
            '--csv_file_path',
            required=True,
            help='Csv file path'
        )

    def handle(self, *args, **options):
        """ Main handler for the command."""
        file_path = options['csv_file_path']

        if not path.isfile(file_path):
            raise CommandError("File not found.")

        with open(file_path) as csv_file:
            course_key = None
            user = None
            file_reader = csv.DictReader(csv_file)
            headers = file_reader.fieldnames

            if not ('course_id' in headers and 'mode' in headers and 'user' in headers):
                raise CommandError('Invalid input CSV file.')

            for row in file_reader:
                try:
                    course_key = CourseKey.from_string(row['course_id'])
                except InvalidKeyError:
                    logger.warning('Invalid or non-existent course id [{}]'.format(row['course_id']))

                try:
                    user = User.objects.get(username=row['user'])
                except:
                    logger.warning('Invalid or non-existent user [{}]'.format(row['user']))
                if course_key and user:
                    try:
                        course_enrollment = CourseEnrollment.get_enrollment(user, course_key)
                        #  If student is not enrolled in course enroll the student in free mode
                        if not course_enrollment:
                            # try to create a enroll user in default course enrollment mode in case of
                            # professional it will break because of no default course mode.
                            try:
                                course_enrollment = CourseEnrollment.get_or_create_enrollment(user=user,
                                                                                              course_key=course_key)
                            except Exception:  # pylint: disable=broad-except
                                # In case if no free mode is available.
                                course_enrollment = None

                        if course_enrollment:
                            # if student already had a enrollment and its mode is same as the provided one
                            if course_enrollment.mode == row['mode']:
                                logger.info("Student [%s] is already enrolled in Course [%s] in mode [%s].", user.username,
                                            course_key, course_enrollment.mode)
                                # set the enrollment to active if its not already active.
                                if not course_enrollment.is_active:
                                    course_enrollment.update_enrollment(is_active=True)
                            else:
                                # if student enrollment exists update it to new mode.
                                with transaction.atomic():
                                    course_enrollment.update_enrollment(
                                        mode=row['mode'],
                                        is_active=True,
                                        skip_refund=True
                                    )
                                    course_enrollment.save()

                                    if row['mode'] == 'credit':
                                        enrollment_attrs = [{
                                            'namespace': 'credit',
                                            'name': 'provider_id',
                                            'value': course_key.org,
                                        }]
                                        CourseEnrollmentAttribute.add_enrollment_attr(enrollment=course_enrollment,
                                                                                      data_list=enrollment_attrs)
                        else:
                            # if student enrollment do not exists directly enroll in new mode.
                            CourseEnrollment.enroll(user=user, course_key=course_key, mode=row['mode'])

                    except Exception as e:
                        logger.info("Unable to update student [%s] course [%s] enrollment to mode [%s] "
                                    "because of Exception [%s]", row['user'], row['course_id'], row['mode'], repr(e))
