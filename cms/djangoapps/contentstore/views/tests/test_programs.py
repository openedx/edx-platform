"""Tests covering the Programs listing on the Studio home."""
from django.conf import settings
from django.core.urlresolvers import reverse
import httpretty
from oauth2_provider.tests.factories import ClientFactory
from provider.constants import CONFIDENTIAL

from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin, ProgramsDataMixin
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class TestProgramListing(ProgramsApiConfigMixin, ProgramsDataMixin, ModuleStoreTestCase):
    """Verify Program listing behavior."""
    def setUp(self):
        super(TestProgramListing, self).setUp()

        ClientFactory(name=ProgramsApiConfig.OAUTH2_CLIENT_NAME, client_type=CONFIDENTIAL)

        self.staff = UserFactory(is_staff=True)
        self.client.login(username=self.staff.username, password='test')

        self.studio_home = reverse('home')

    @httpretty.activate
    def test_programs_config_disabled(self):
        """Verify that the programs tab and creation button aren't rendered when config is disabled."""
        self.create_config(enable_studio_tab=False)
        self.mock_programs_api()

        response = self.client.get(self.studio_home)

        self.assertNotIn("You haven't created any programs yet.", response.content)

        for program_name in self.PROGRAM_NAMES:
            self.assertNotIn(program_name, response.content)

    @httpretty.activate
    def test_programs_requires_staff(self):
        """
        Verify that the programs tab and creation button aren't rendered unless the user has
        global staff permissions.
        """
        student = UserFactory(is_staff=False)
        self.client.login(username=student.username, password='test')

        self.create_config()
        self.mock_programs_api()

        response = self.client.get(self.studio_home)
        self.assertNotIn("You haven't created any programs yet.", response.content)

    @httpretty.activate
    def test_programs_displayed(self):
        """Verify that the programs tab and creation button can be rendered when config is enabled."""
        self.create_config()

        # When no data is provided, expect creation prompt.
        self.mock_programs_api(data={'results': []})

        response = self.client.get(self.studio_home)
        self.assertIn("You haven't created any programs yet.", response.content)

        # When data is provided, expect a program listing.
        self.mock_programs_api()

        response = self.client.get(self.studio_home)
        for program_name in self.PROGRAM_NAMES:
            self.assertIn(program_name, response.content)


class TestProgramAuthoringView(ProgramsApiConfigMixin, ModuleStoreTestCase):
    """Verify the behavior of the program authoring app's host view."""
    def setUp(self):
        super(TestProgramAuthoringView, self).setUp()

        self.staff = UserFactory(is_staff=True)
        self.programs_path = reverse('programs')

    def _assert_status(self, status_code):
        """Verify the status code returned by the Program authoring view."""
        response = self.client.get(self.programs_path)
        self.assertEquals(response.status_code, status_code)

        return response

    def test_authoring_login_required(self):
        """Verify that accessing the view requires the user to be authenticated."""
        response = self.client.get(self.programs_path)
        self.assertRedirects(
            response,
            '{login_url}?next={programs}'.format(
                login_url=settings.LOGIN_URL,
                programs=self.programs_path
            )
        )

    def test_authoring_header(self):
        """Verify that the header contains the expected text."""
        self.client.login(username=self.staff.username, password='test')
        self.create_config()

        response = self._assert_status(200)
        self.assertIn("Program Administration", response.content)

    def test_authoring_access(self):
        """
        Verify that a 404 is returned if Programs authoring is disabled, or the user does not have
        global staff permissions.
        """
        self.client.login(username=self.staff.username, password='test')
        self._assert_status(404)

        # Enable Programs authoring interface
        self.create_config()

        student = UserFactory(is_staff=False)
        self.client.login(username=student.username, password='test')
        self._assert_status(404)
