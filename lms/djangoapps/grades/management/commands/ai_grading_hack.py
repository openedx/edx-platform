"""
A hackathon-specific management command. I've found some nifty test data on
Kaggle (see https://www.kaggle.com/c/asap-aes) to use for training our AI
grader; this command will insert that data as a bunch of staff-graded assessments.

This command (in edx-platform) will create all the users, and enroll them in the course.

The remainder is handled by an ora2 command.
"""

from django.core.management.base import BaseCommand

from enrollment.api import add_enrollment
from enrollment.errors import CourseEnrollmentExistsError
from optparse import make_option
from student.tests.factories import UserFactory


class Command(BaseCommand):
    """
    This is a docstring, kinda
    """
    option_list = BaseCommand.option_list + (
        make_option('-c', '--course',
            metavar='COURSE_ID',
            dest='course',
            default=False,
            help='Course ID'),
        make_option('-i', '--input',
            metavar='FILE',
            dest='input',
            default=False,
            help='Filename for input'))

    def handle(self, *args, **options):
        with open("erics_hackathon_data.csv", "w") as outfile:
            for _ in open(options['input']):
                # create student
                student = UserFactory.create()

                # enroll in course
                try:
                    add_enrollment(student.username, options['course'])
                except CourseEnrollmentExistsError:
                    pass
                outfile.write(unicode(student.id) + "\n")
