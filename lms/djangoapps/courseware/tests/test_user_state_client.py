"""
Black-box tests of the DjangoUserStateClient against the semantics
defined in edx_user_state_client.
"""


from collections import defaultdict

from django.db import connections

from edx_user_state_client.tests import UserStateClientTestBase

from lms.djangoapps.courseware.tests.factories import UserFactory
from lms.djangoapps.courseware.user_state_client import DjangoXBlockUserStateClient
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


class TestDjangoUserStateClient(UserStateClientTestBase, ModuleStoreTestCase):
    """
    Tests of the DjangoUserStateClient backend.
    It reuses all tests from :class:`~UserStateClientTestBase`.
    """
    __test__ = True
    # Tell Django to clean out all databases, not just default
    databases = {alias for alias in connections}

    def _user(self, user_idx):
        return self.users[user_idx].username

    def _block_type(self, block):
        # We only record block state history in DjangoUserStateClient
        # when the block type is 'problem'
        return 'problem'

    def setUp(self):
        super(TestDjangoUserStateClient, self).setUp()
        self.client = DjangoXBlockUserStateClient()
        self.users = defaultdict(UserFactory.create)
