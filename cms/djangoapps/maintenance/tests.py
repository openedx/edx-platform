"""
Tests for the maintenance app views.
"""


import ddt
from django.conf import settings
from django.urls import reverse

from common.djangoapps.student.tests.factories import AdminFactory, UserFactory
from openedx.features.announcements.models import Announcement
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order

from .views import MAINTENANCE_VIEWS

# This list contains URLs of all maintenance app views.
MAINTENANCE_URLS = [reverse(view['url']) for view in MAINTENANCE_VIEWS.values()]


class TestMaintenanceIndex(ModuleStoreTestCase):
    """
    Tests for maintenance index view.
    """

    def setUp(self):
        super().setUp()
        self.user = AdminFactory()
        login_success = self.client.login(username=self.user.username, password=self.TEST_PASSWORD)
        self.assertTrue(login_success)
        self.view_url = reverse('maintenance:maintenance_index')

    def test_maintenance_index(self):
        """
        Test that maintenance index view lists all the maintenance app views.
        """
        response = self.client.get(self.view_url)
        self.assertContains(response, 'Maintenance', status_code=200)

        # Check that all the expected links appear on the index page.
        for url in MAINTENANCE_URLS:
            self.assertContains(response, url, status_code=200)


@ddt.ddt
class MaintenanceViewTestCase(ModuleStoreTestCase):
    """
    Base class for maintenance view tests.
    """
    view_url = ''

    def setUp(self):
        super().setUp()
        self.user = AdminFactory()
        login_success = self.client.login(username=self.user.username, password=self.TEST_PASSWORD)
        self.assertTrue(login_success)

    def verify_error_message(self, data, error_message):
        """
        Verify the response contains error message.
        """
        response = self.client.post(self.view_url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, error_message, status_code=200)

    def tearDown(self):
        """
        Reverse the setup.
        """
        self.client.logout()
        super().tearDown()


@ddt.ddt
class MaintenanceViewAccessTests(MaintenanceViewTestCase):
    """
    Tests for access control of maintenance views.
    """
    @ddt.data(*MAINTENANCE_URLS)
    def test_require_login(self, url):
        """
        Test that maintenance app requires user login.
        """
        # Log out then try to retrieve the page
        self.client.logout()
        response = self.client.get(url)

        # Expect a redirect to the login page
        redirect_url = '{login_url}?next={original_url}'.format(
            login_url=settings.LOGIN_URL,
            original_url=url,
        )

        # Studio login redirects to LMS login
        self.assertRedirects(response, redirect_url, target_status_code=302)

    @ddt.data(*MAINTENANCE_URLS)
    def test_global_staff_access(self, url):
        """
        Test that all maintenance app views are accessible to global staff user.
        """
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    @ddt.data(*MAINTENANCE_URLS)
    def test_non_global_staff_access(self, url):
        """
        Test that all maintenance app views are not accessible to non-global-staff user.
        """
        user = UserFactory(username='test', email='test@example.com', password=self.TEST_PASSWORD)
        login_success = self.client.login(username=user.username, password=self.TEST_PASSWORD)
        self.assertTrue(login_success)

        response = self.client.get(url)
        self.assertContains(
            response,
            f'Must be {settings.PLATFORM_NAME} staff to perform this action.',
            status_code=403
        )


@ddt.ddt
class TestAnnouncementsViews(MaintenanceViewTestCase):
    """
    Tests for the announcements edit view.
    """

    def setUp(self):
        super().setUp()
        self.admin = AdminFactory.create(
            email='staff@edx.org',
            username='admin',
            password=self.TEST_PASSWORD
        )
        self.client.login(username=self.admin.username, password=self.TEST_PASSWORD)
        self.non_staff_user = UserFactory.create(
            email='test@edx.org',
            username='test',
            password=self.TEST_PASSWORD
        )

    def test_index(self):
        """
        Test create announcement view
        """
        url = reverse("maintenance:announcement_index")
        response = self.client.get(url)
        self.assertContains(response, '<div class="announcement-container">')

    def test_create(self):
        """
        Test create announcement view
        """
        url = reverse("maintenance:announcement_create")
        self.client.post(url, {"content": "Test Create Announcement", "active": True})
        result = Announcement.objects.filter(content="Test Create Announcement").exists()
        self.assertTrue(result)

    def test_edit(self):
        """
        Test edit announcement view
        """
        announcement = Announcement.objects.create(content="test")
        announcement.save()
        url = reverse("maintenance:announcement_edit", kwargs={"pk": announcement.pk})
        response = self.client.get(url)
        self.assertContains(response, '<div class="wrapper-form announcement-container">')
        self.client.post(url, {"content": "Test Edit Announcement", "active": True})
        announcement = Announcement.objects.get(pk=announcement.pk)
        self.assertEqual(announcement.content, "Test Edit Announcement")

    def test_delete(self):
        """
        Test delete announcement view
        """
        announcement = Announcement.objects.create(content="Test Delete")
        announcement.save()
        url = reverse("maintenance:announcement_delete", kwargs={"pk": announcement.pk})
        self.client.post(url)
        result = Announcement.objects.filter(content="Test Edit Announcement").exists()
        self.assertFalse(result)

    def _test_403(self, viewname, kwargs=None):
        url = reverse("maintenance:%s" % viewname, kwargs=kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_authorization(self):
        self.client.login(username=self.non_staff_user, password=self.TEST_PASSWORD)
        announcement = Announcement.objects.create(content="Test Delete")
        announcement.save()

        self._test_403("announcement_index")
        self._test_403("announcement_create")
        self._test_403("announcement_edit", {"pk": announcement.pk})
        self._test_403("announcement_delete", {"pk": announcement.pk})
