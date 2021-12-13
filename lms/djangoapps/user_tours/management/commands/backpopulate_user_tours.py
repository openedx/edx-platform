""" Management command to backpopulate User Tours. """

import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.user_tours.models import UserTour

User = get_user_model()


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py lms backpopulate_user_tours
    """
    help = 'Creates or updates a row in the UserTour table for all users in the platform.'

    def add_arguments(self, parser):
        parser.add_argument('--batch-delay', type=float, default=1.0, help='Time delay in each iteration')
        parser.add_argument('--batch-size', type=int, default=10000, help='Batch size')

    def handle(self, *args, **options):
        """
        Backpopulates UserTour objects for all existing users who don't already have a UserTour.

        If the user has any prior enrollments, we will treat them as an existing user,
        otherwise they will receive a new user treatment.
        """
        batch_delay = options['batch_delay']
        batch_size = options['batch_size']
        while User.objects.filter(tour__isnull=True).exists():
            time.sleep(batch_delay)
            for user in User.objects.filter(tour__isnull=True)[:batch_size]:
                if CourseEnrollment.objects.filter(user=user).exists():
                    course_home_tour_status = UserTour.CourseHomeChoices.EXISTING_USER_TOUR
                    show_courseware_tour = False
                else:
                    course_home_tour_status = UserTour.CourseHomeChoices.NEW_USER_TOUR
                    show_courseware_tour = True

                UserTour.objects.update_or_create(
                    user=user,
                    defaults={
                        'course_home_tour_status': course_home_tour_status,
                        'show_courseware_tour': show_courseware_tour,
                    },
                )
