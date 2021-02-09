"""
All tests for mailchimp pipeline helpers
"""
from datetime import datetime

import pytest
from django.contrib.auth.models import User

from common.djangoapps.student.models import UserProfile
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from openedx.adg.common.course_meta.tests.factories import CourseMetaFactory
from openedx.adg.common.mailchimp_pipeline.helpers import (
    get_enrollment_course_names_and_short_ids_by_user,
    get_extendeduserprofile_merge_fields,
    get_user_merge_fields,
    get_userapplication_merge_fields,
    get_userprofile_merge_fields,
    is_mailchimp_sync_required
)
from openedx.adg.constants import MONTH_DAY_YEAR_FORMAT
from openedx.adg.lms.applications.models import UserApplication
from openedx.adg.lms.applications.tests.factories import UserApplicationFactory
from openedx.adg.lms.registration_extension.models import ExtendedUserProfile
from openedx.adg.lms.registration_extension.tests.factories import ExtendedUserProfileFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms


@pytest.fixture
def user_enrollments():
    """
    A fixture for enrolling user into multiple running courses.
    """
    user = UserFactory()
    enrollment_data = {'user': user, 'is_active': True, 'course__end_date': datetime(2022, 1, 1)}
    enrollment1 = CourseEnrollmentFactory(course__display_name='course1', **enrollment_data)
    enrollment2 = CourseEnrollmentFactory(course__display_name='course2', **enrollment_data)
    enrollment3 = CourseEnrollmentFactory(course__display_name='course3', **enrollment_data)
    enrolled_courses = [enrollment1.course, enrollment2.course, enrollment3.course]

    for course in enrolled_courses:
        CourseMetaFactory(course=course)

    return user, enrolled_courses


@pytest.mark.django_db
def test_get_enrollment_course_names_and_short_ids_by_user(user_enrollments):  # pylint: disable=redefined-outer-name
    """
    Assert that all active and running enrolled courses for a user are returned.
    """
    user, _ = user_enrollments
    course_short_ids, course_titles = get_enrollment_course_names_and_short_ids_by_user(user)

    assert course_short_ids == '100,101,102'
    assert course_titles == 'course1,course2,course3'


def test_is_mailchimp_sync_required():
    """
    Test is mailchimp sync required util.
    """
    dummy_kwargs = {'update_fields': []}
    assert is_mailchimp_sync_required(True, User, **dummy_kwargs)
    assert not is_mailchimp_sync_required(False, User, **dummy_kwargs)
    assert is_mailchimp_sync_required(True, UserProfile, **dummy_kwargs)
    assert is_mailchimp_sync_required(False, UserProfile, **dummy_kwargs)
    assert is_mailchimp_sync_required(True, UserApplication, **dummy_kwargs)
    assert is_mailchimp_sync_required(True, ExtendedUserProfile, **dummy_kwargs)

    dummy_kwargs = {'update_fields': ('organization',)}
    assert is_mailchimp_sync_required(False, UserApplication, **dummy_kwargs)
    dummy_kwargs = {'update_fields': ('company',)}
    assert is_mailchimp_sync_required(False, ExtendedUserProfile, **dummy_kwargs)


@pytest.mark.django_db
@skip_unless_lms
def test_get_user_merge_fields():
    """
    Test user merge fields computation.
    """
    user = UserFactory()
    user_merge_fields = {'USERNAME': user.username, 'DATEREGIS': str(user.date_joined.strftime(MONTH_DAY_YEAR_FORMAT))}
    assert get_user_merge_fields(user) == user_merge_fields


@pytest.mark.django_db
@skip_unless_lms
def test_get_extendeduserprofile_merge_fields():
    """
    Test extended profile merge fields computation.
    """
    extended_profile = ExtendedUserProfileFactory()
    extended_profile_merge_fields = {'COMPANY': extended_profile.company.title or ''}
    assert get_extendeduserprofile_merge_fields(extended_profile) == extended_profile_merge_fields


@pytest.mark.django_db
@skip_unless_lms
def test_get_userapplication_merge_fields():
    """
    Test user application merge fields computation.
    """
    user_application = UserApplicationFactory()
    user_application_merge_fields = {
        'ORG_NAME': user_application.organization or '',
        'APP_STATUS': user_application.status,
        'B_LINE': user_application.business_line.title or ''
    }
    assert get_userapplication_merge_fields(user_application) == user_application_merge_fields


@pytest.mark.django_db
@skip_unless_lms
def test_get_userprofile_merge_fields():
    """
    Test user profile merge fields computation.
    """
    user_profile = UserFactory().profile
    user_profile_merge_fields = {
        'LOCATION': user_profile.city,  # pylint: disable=no-member
        'FULLNAME': user_profile.name,
    }
    assert get_userprofile_merge_fields(user_profile) == user_profile_merge_fields
