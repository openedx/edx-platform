import ddt
import mock
import pytest
from django.conf import settings
from django.http.response import HttpResponse
from django.urls import reverse

from openedx.features.pakx.cms.custom_settings.models import CourseOverviewContent
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from .factories import CourseOverviewContentFactory


@ddt.ddt
@pytest.mark.django_db
class CourseCustomSettingsViewTests(ModuleStoreTestCase):

    def setUp(self):
        super(CourseCustomSettingsViewTests, self).setUp()

        self.course = CourseFactory()
        self.course_key = self.course.location.course_key
        self.path = reverse('custom_settings', kwargs={'course_key_string': self.course_key})
        self.client.login(username=self.user.username, password=self.user_password)

    @mock.patch('openedx.features.pakx.cms.custom_settings.views.render_to_string')
    @mock.patch('openedx.features.pakx.cms.custom_settings.views.render')
    @mock.patch('openedx.features.pakx.cms.custom_settings.views.get_course_and_check_access')
    @ddt.data(True, False)
    def test_get_course_custom_settings_successfully(self, is_course_overview_content_changes,
                                                     mock_get_course_and_check_access,
                                                     mock_render,
                                                     mock_render_to_string):
        body_html = 'Course overview dummy html'
        if is_course_overview_content_changes:
            body_html = 'Custom HTML for course overview'
            CourseOverviewContentFactory(course__id=self.course_key, body_html=body_html)

        mock_get_course_and_check_access.return_value = self.course
        mock_render_to_string.return_value = 'Course overview dummy html'
        mock_render.return_value = HttpResponse('Return get response')

        self.client.get(self.path)

        mock_render.assert_called_once_with(mock.ANY, 'custom_settings.html', context={
            'context_course': self.course,
            'default_content': body_html,
            'course_overview_url': '{}/courses/{}/overview'.format(settings.LMS_ROOT_URL, self.course_key),
            'custom_settings_url': reverse('custom_settings', kwargs={'course_key_string': self.course_key})
        })

    def test_get_course_custom_settings_no_access_to_course(self):
        self.client.logout()
        non_staff_user, password = self.create_non_staff_user()
        self.client.login(username=non_staff_user.username, password=password)
        response = self.client.get(self.path)

        assert response.status_code == 403

    @mock.patch('openedx.features.pakx.cms.custom_settings.views.redirect')
    def test_post_course_custom_settings_successfully(self, mock_redirect):
        mock_redirect.return_value = HttpResponse('Return post response')
        body_html = 'Course overview dummy html posted'

        self.client.post(self.path, {'course-overview': body_html})

        course_overview_content = CourseOverviewContent.objects.filter(course_id=self.course_key).first()
        assert course_overview_content.body_html == body_html
