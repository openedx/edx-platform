import datetime

import pytz
from django.test import RequestFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from openedx.core.lib.courses import course_image_url
from student.roles import CourseInstructorRole, CourseStaffRole
from student.tests.factories import UserFactory
from ..utils import serialize_datetime
from ...serializers.course_runs import CourseRunSerializer


class CourseRunSerializerTests(ModuleStoreTestCase):
    def test_data(self):
        start = datetime.datetime.now(pytz.UTC)
        end = start + datetime.timedelta(days=30)
        enrollment_start = start - datetime.timedelta(days=7)
        enrollment_end = end - datetime.timedelta(days=14)

        course = CourseFactory(start=start, end=end, enrollment_start=enrollment_start, enrollment_end=enrollment_end)
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
            }
        }
        assert serializer.data == expected
