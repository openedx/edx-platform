"""Tests covering the Programs listing on the Studio home."""
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

        self.user = UserFactory(is_staff=True)
        self.client.login(username=self.user.username, password='test')

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
        """Verify that the programs tab and creation button aren't rendered unless the user has global staff."""
        self.user = UserFactory(is_staff=False)
        self.client.login(username=self.user.username, password='test')

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
