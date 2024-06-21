"""
User Verification Server for Profile Information
"""
import os
import logging
from django.test import LiveServerTestCase
from django.urls import reverse
from pact import Verifier

from common.djangoapps.student.tests.factories import UserFactory
from common.djangoapps.student.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
PACT_DIR = os.path.dirname(os.path.realpath(__file__))
PACT_FILE = "frontend-app-profile-edx-platform.json"


class ProviderState():
    """ Provider State for the testing profile """

    def account_setup(self, request):
        """ Sets up the Profile that we want to mock in accordance to our contract """
        User.objects.filter(username="pact_staff").delete()
        user_acc = UserFactory.create(username="pact_staff")
        user_acc.profile.name = "Lemon Seltzer"
        user_acc.profile.bio = "This is my bio"
        user_acc.profile.country = "ME"
        user_acc.profile.is_active = True
        user_acc.profile.goals = "Learn and Grow!"
        user_acc.profile.year_of_birth = 1901
        user_acc.profile.phone_number = "+11234567890"
        user_acc.profile.mailing_address = "Park Ave"
        user_acc.profile.save()
        return user_acc


@csrf_exempt
@require_POST
def provider_state(request):
    """ Provider State view for our verifier"""
    state_setup = {"I have a user's basic information": ProviderState().account_setup}
    request_body = json.loads(request.body)
    state = request_body.get('state')
    User.objects.filter(username="pact_staff").delete()
    print('Setting up provider state for state value: {}'.format(state))
    state_setup["I have a user's basic information"](request)
    return JsonResponse({'result': state})


class ProviderVerificationServer(LiveServerTestCase):
    """ Live Server for Pact Account Verification """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.PACT_URL = cls.live_server_url

        cls.verifier = Verifier(
            provider='edx-platform',
            provider_base_url=cls.PACT_URL,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_pact(self):
        output, _ = self.verifier.verify_pacts(
            os.path.join(PACT_DIR, PACT_FILE),
            headers=['Pact-Authentication: Allow', ],
            provider_states_setup_url=f"{self.PACT_URL}{reverse('acc-provider-state-view')}",
        )
        assert output == 0
