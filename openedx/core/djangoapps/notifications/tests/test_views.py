from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User

from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.notifications.serializers import CourseEnrollmentSerializer
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class CourseEnrollmentListViewTest(ModuleStoreTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory()
        # self.client.force_authenticate(user=self.user)
        course_1 = CourseFactory.create(
            org='testorg',
            number='testcourse',
            run='testrun'
        )
        course_2 = CourseFactory.create(
            org='testorg',
            number='testcourse_two',
            run='testrun'
        )
        course_overview_1 = CourseOverviewFactory.create(id=course_1.id, org='AwesomeOrg')
        course_overview_2 = CourseOverviewFactory.create(id=course_2.id, org='AwesomeOrg')

        self.enrollment1 = CourseEnrollment.objects.create(
            user=self.user,
            course=course_overview_1,
            is_active=True,
            mode='audit'
        )
        self.enrollment2 = CourseEnrollment.objects.create(
            user=self.user,
            course=course_overview_2,
            is_active=False,
            mode='honor'
        )

    def test_course_enrollment_list_view(self):
        self.client = APIClient()
        self.client.login(username=self.user.username, password='test')
        url = reverse('enrollment-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        enrollments = CourseEnrollment.objects.filter(user=self.user, is_active=True)
        breakpoint()
        expected_data = CourseEnrollmentSerializer(enrollments, many=True).data
        self.assertEqual(response.data, expected_data)

    def test_course_enrollment_api_permission(self):
        url = reverse('enrollment-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
