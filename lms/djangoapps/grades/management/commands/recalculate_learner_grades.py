"""
Command to recalculate a user's grades for a course, for every user in
a csv of (user, course) pairs.
"""


import csv

from django.core.management.base import BaseCommand

from lms.djangoapps.grades.tasks import recalculate_course_and_subsection_grades_for_user


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py lms recalculate_learner_grades learner_courses_to_recalculate.csv
    """
    help = 'Recalculates a user\'s grades for a course, for every user in a csv of (user, course) pairs'

    def add_arguments(self, parser):
        parser.add_argument('csv')

    def handle(self, *args, **options):
        filename = options['csv']

        with open(filename) as csv_file:
            self.regrade_learner_in_course_from_csv(csv_file)

    def regrade_learner_in_course_from_csv(self, csv_file):
        csv_reader = csv.DictReader(csv_file)

        for row in csv_reader:
            recalculate_course_and_subsection_grades_for_user.apply_async(
                kwargs={'user_id': row['user_id'], 'course_key': row['course_id']}
            )
