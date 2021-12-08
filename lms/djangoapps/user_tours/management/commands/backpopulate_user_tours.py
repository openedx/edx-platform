""" Management command to backpopulate User Tours. """

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

    def handle(self, *args, **options):
        """
        Backpopulates UserTour objects for all existing users who don't already have a UserTour.

        If the user has any prior enrollments, we will treat them as an existing user,
        otherwise they will receive a new user treatment.
        """
        for user in User.objects.filter(tour__isnull=True):
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
