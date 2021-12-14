""" Tests for UserTour Signal Handlers. """

from django.test import TestCase

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.user_tours.models import UserTour


class TestUserTourHandlers(TestCase):
    """ Tests for UserTour Signal Handlers. """
    def test_successful_handle(self):
        """
        Tests a UserTour is created when a new User is created.
        Then ensures a new UserTour is not created when the user is updated.
        """
        assert UserTour.objects.count() == 0
        user = UserFactory()
        tour = UserTour.objects.get(user=user)
        assert tour.course_home_tour_status == UserTour.CourseHomeChoices.NEW_USER_TOUR
        assert tour.show_courseware_tour is True
        user.username = 'new-username'
        user.save()
        assert UserTour.objects.count() == 1
