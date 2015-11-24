"""
Test spike
"""

import json
from django.core.urlresolvers import reverse
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from .test_views import CourseApiTestViewMixin

class CourseListViewTestCase(CourseApiTestViewMixin, SharedModuleStoreTestCase):
    """
    Test responses returned from CourseListView.
    """

    expected_results = {
        "results": [
            {
                "course_id": "edX/toy/2012_Fall",
                "name": "Toy Course",
                "number": "toy",
                "org": "edX",
                "description": "A course about toys.",
                "media": {
                    "course_image": {
                        "uri": "/c4x/edX/toy/asset/just_a_test.jpg",
                    }
                },
                "start": "2015-07-17T12:00:00Z",
                "start_type": "timestamp",
                "start_display": "July 17, 2015",
                "end": "2015-09-19T18:00:00Z",
                "enrollment_start": "2015-06-15T00:00:00Z",
                "enrollment_end": "2015-07-15T00:00:00Z",
                "blocks_url": "/api/courses/v1/blocks/?course_id=edX%2Ftoy%2F2012_Fall"
            }
        ],
        "pagination": {
            "next": None,
            "previous": None,
            "count": 1,
            "num_pages": 1
        }
    }
    @classmethod
    def setUpClass(cls):
        super(CourseListViewTestCase, cls).setUpClass()
        cls.course = cls.create_course()
        cls.url = reverse('course-list')
        cls.staff_user = cls.create_user(username='staff', is_staff=True)
        cls.honor_user = cls.create_user(username='honor', is_staff=False)

    def test_as_staff(self):
        self.setup_user(self.staff_user)
        params = {'page': 1}
        response = self.client.get(self.url, data=params)
        self.assertEqual(json.loads(response.content), self.expected_results)
