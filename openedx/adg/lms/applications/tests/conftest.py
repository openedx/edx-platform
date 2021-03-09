"""
File containing common fixtures used across different test modules
"""
from datetime import date, timedelta

import pytest

from common.djangoapps.student.tests.factories import GroupFactory, UserFactory
from openedx.adg.lms.applications.admin import (
    EducationInline,
    UserApplicationADGAdmin,
    WorkExperienceInline,
    adg_admin_site
)
from openedx.adg.lms.applications.constants import ADG_ADMIN_GROUP_NAME
from openedx.adg.lms.applications.models import UserApplication
from openedx.adg.lms.applications.tests.factories import MultilingualCourseGroupFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory

from .constants import ADMIN_TYPE_SUPER_ADMIN, TITLE_BUSINESS_LINE_1, TITLE_BUSINESS_LINE_2
from .factories import EducationFactory, UserApplicationFactory, WorkExperienceFactory


@pytest.fixture
def education():
    return EducationFactory()


@pytest.fixture
def work_experience():
    return WorkExperienceFactory()


@pytest.fixture
def user_application():
    return UserApplicationFactory()


@pytest.fixture
def user_application_adg_admin_instance():
    return UserApplicationADGAdmin(UserApplication, adg_admin_site)


@pytest.fixture
def current_date():
    return date.today()


@pytest.fixture
def education_inline():
    return EducationInline(UserApplication, adg_admin_site)


@pytest.fixture
def work_experience_inline():
    return WorkExperienceInline(UserApplication, adg_admin_site)


@pytest.fixture
def user_applications_with_different_business_lines():
    UserApplicationFactory(business_line__title=TITLE_BUSINESS_LINE_1)
    UserApplicationFactory(business_line__title=TITLE_BUSINESS_LINE_2)
    return UserApplication.objects.all()


@pytest.fixture
def admin_user(admin_type):
    """
    Fixture to create admin users, super admin or ADG on the base of admin_type
    Args:
        admin_type:  str, type of the admin

    Returns:
        User object, with permissions according to the admin type
    """
    if admin_type is ADMIN_TYPE_SUPER_ADMIN:
        return UserFactory(is_superuser=True)
    else:   # ADG admin
        return UserFactory(is_staff=True, groups=[GroupFactory(name=ADG_ADMIN_GROUP_NAME)])


@pytest.fixture(name='courses')
def course_overviews(current_time):
    """
    Fixture which return multiple courses
    """
    course_start_end_date = {
        'start_date': current_time - timedelta(days=1),
        'end_date': current_time + timedelta(days=1),
    }
    return {
        'test_course1': CourseOverviewFactory(language='en', **course_start_end_date),
        'test_course2': CourseOverviewFactory(language='ar', **course_start_end_date),
    }


@pytest.fixture(name='expired_course')
def expired_course_overview(current_time):
    return CourseOverviewFactory(
        language='en',
        start_date=current_time - timedelta(days=2),
        end_date=current_time - timedelta(days=1),
    )


@pytest.fixture(name='course_group')
def multilingual_course_group():
    return MultilingualCourseGroupFactory()
