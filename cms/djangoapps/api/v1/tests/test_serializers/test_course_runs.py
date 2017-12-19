import datetime

import ddt
import pytz
from django.test import RequestFactory

from openedx.core.lib.courses import course_image_url
from student.roles import CourseInstructorRole, CourseStaffRole
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ...serializers.course_runs import CourseRunSerializer
from ..utils import serialize_datetime


@ddt.ddt
class CourseRunSerializerTests(ModuleStoreTestCase):

    @ddt.data(
        ('instructor_paced', False),
        ('self_paced', True),
    )
    @ddt.unpack
    def test_data(self, expected_pacing_type, self_paced):
        start = datetime.datetime.now(pytz.UTC)
        end = start + datetime.timedelta(days=30)
        enrollment_start = start - datetime.timedelta(days=7)
        enrollment_end = end - datetime.timedelta(days=14)

        course = CourseFactory(
            start=start,
            end=end,
            enrollment_start=enrollment_start,
            enrollment_end=enrollment_end,
            self_paced=self_paced
        )
        instructor = UserFactory()
        CourseInstructorRole(course.id).add_users(instructor)
        staff = UserFactory()
        CourseStaffRole(course.id).add_users(staff)

        request = RequestFactory().get('')
        serializer = CourseRunSerializer(course, context={'request': request})
        expected = {
            'id': str(course.id),
            'title': course.display_name,
            'schedule': {
                'start': serialize_datetime(start),
                'end': serialize_datetime(end),
                'enrollment_start': serialize_datetime(enrollment_start),
                'enrollment_end': serialize_datetime(enrollment_end),
            },
            'team': [
                {
                    'user': instructor.username,
                    'role': 'instructor',
                },
                {
                    'user': staff.username,
                    'role': 'staff',
                },
            ],
            'images': {
                'card_image': request.build_absolute_uri(course_image_url(course)),
            },
            'pacing_type': expected_pacing_type,
        }
        assert serializer.data == expected
