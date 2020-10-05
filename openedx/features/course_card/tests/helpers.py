"""
Helper file which contains the helper methods used in different Course card Unit Tests
"""
from datetime import datetime, timedelta

from custom_settings.models import CustomSettings
from lms.djangoapps.onboarding.models import EmailPreference, Organization, UserExtendedProfile
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import UserProfile
from student.tests.factories import UserFactory

from ..models import CourseCard


def set_course_dates(course, enrollment_start, enrollment_end, course_start, course_end):
    """
    Helper function to set the dates required for course

    Arguments:
        course (Course): Contains the course object
        enrollment_start (int): Contains the enrollment_start days
        enrollment_end (int): Contains the enrollment_end days
        course_start (int): Contains the course_start days
        course_end (int): Contains the course_end days

    Returns:
       CourseOverview: A course CourseOverview object
    """
    course_overview = CourseOverview.get_from_id(course_id=course.id)

    course_overview.enrollment_start = datetime.utcnow() + timedelta(days=enrollment_start)
    course_overview.enrollment_end = datetime.utcnow() + timedelta(days=enrollment_end)
    course_overview.start = datetime.utcnow() + timedelta(days=course_start)
    course_overview.end = datetime.utcnow() + timedelta(days=course_end)

    course_overview.save()

    return course_overview


def disable_course_card(course):
    """
    Arguments:
        course (CourseCard): Contains the course card details
    """
    course_card = CourseCard.objects.get(course_id=course.id)
    course_card.is_enabled = False
    course_card.save()


def initialize_test_user(password='test', is_staff=False):
    """
    Arguments:
        password (:string): password to set
        is_staff (:boolean): is_staff or not

    Returns:
        User: A new User object with profile details
    """
    user = UserFactory(is_staff=is_staff, password=password)
    email_preference = EmailPreference(
        user=user,
        opt_in="no",

    )
    email_preference.save()

    user_profile = UserProfile.objects.get(user=user)
    user_profile.name = "{} {}".format(user.first_name, user.last_name)
    user_profile.level_of_education = 'b'

    user_profile.save()

    extended_profile = UserExtendedProfile(
        user=user,
        is_interests_data_submitted=True,
        english_proficiency="Master",
    )
    extended_profile.save()

    organization = Organization(
        admin=user,
        alternate_admin_email=user.email,
    )
    organization.save()
    organization.unclaimed_org_admin_email = user.email
    organization.alternate_admin_email = None
    organization.save()

    return user


def save_course_custom_settings(course_key_string, course_open_date=datetime.utcnow() + timedelta(days=1)):
    course_settings = CustomSettings(id=course_key_string, course_short_id=1, course_open_date=course_open_date)
    course_settings.save()
    return course_settings
