import pytest

from course_modes.models import CourseMode
from custom_settings.models import CustomSettings
from custom_settings.signals.handlers import initialize_course_settings
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.features.philu_utils.py_test import does_not_raise


@pytest.mark.django_db
@pytest.mark.parametrize('created', [False, True])
def test_initialize_course_settings(created):
    """Assert that CustomSettings and CourseMode objects are created when handler is called"""
    course_overview = CourseOverviewFactory(display_name='test_overview')

    with does_not_raise():
        initialize_course_settings(None, course_overview, created)

        if created:
            assert CustomSettings.objects.filter(id=course_overview.id).count() == 1
            assert CourseMode.objects.filter(course_id=course_overview.id, mode_slug='honor',
                                             mode_display_name='test_overview').count() == 1
