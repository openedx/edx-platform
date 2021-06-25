"""
course_overview api tests
"""

from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.api import (
    get_course_overview,
    get_course_overview_or_none,
    get_course_overviews
)
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from ..models import CourseOverview


class TestCourseOverviewsApi(ModuleStoreTestCase):
    """
    TestCourseOverviewsApi tests.
    """

    def setUp(self):
        super().setUp()
        for _ in range(3):
            CourseOverviewFactory.create()

    def test_get_course_overview(self):
        """
        Test for `get_course_overview` function to retrieve a single course overview.
        """
        course_overview = CourseOverviewFactory.create()
        retrieved_course_overview = get_course_overview(course_overview.id)
        assert course_overview.id == retrieved_course_overview.id

    def test_get_course_overview_or_none(self):
        """
        Test for `test_get_course_overview_or_none` function when the overview exists.
        """
        course_overview = CourseOverviewFactory.create()
        retrieved_course_overview = get_course_overview_or_none(course_overview.id)
        assert course_overview.id == retrieved_course_overview.id

    def test_get_course_overview_or_none_missing(self):
        """
        Test for `test_get_course_overview_or_none` function when the overview does not exist.
        """
        course_run_key = CourseKey.from_string('course-v1:coping+with+deletions')
        retrieved_course_overview = get_course_overview_or_none(course_run_key)
        assert retrieved_course_overview is None

    def test_get_course_overviews(self):
        """
        get_course_overviews should return the expected CourseOverview data
        in serialized form (a list of dicts)
        """
        course_ids = []
        course_ids.append(str(CourseOverview.objects.first().id))
        course_ids.append(str(CourseOverview.objects.last().id))

        data = get_course_overviews(course_ids)
        assert len(data) == 2
        for overview in data:
            assert overview['id'] in course_ids

        fields = [
            'display_name_with_default',
            'has_started',
            'has_ended',
            'pacing',
        ]
        for field in fields:
            assert field in data[0]
