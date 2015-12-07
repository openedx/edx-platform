"""
Black-box tests of the DjangoUserStateClient against the semantics
defined in edx_user_state_client.
"""

from collections import defaultdict
from unittest import skip

from django.test import TestCase

from edx_user_state_client.tests import UserStateClientTestBase
from courseware.user_state_client import DjangoXBlockUserStateClient
from courseware.tests.factories import UserFactory


class TestDjangoUserStateClient(UserStateClientTestBase, TestCase):
    """
    Tests of the DjangoUserStateClient backend.
    """
    __test__ = True

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

    # We're skipping these tests because the iter_all_by_block and iter_all_by_course
    # are not implemented in the DjangoXBlockUserStateClient
    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_blocks_deleted_block(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_blocks_empty(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_blocks_many_users(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_blocks_single_user(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_course_deleted_block(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_course_empty(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_course_single_user(self):
        pass

    @skip("Not supported by DjangoXBlockUserStateClient")
    def test_iter_course_many_users(self):
        pass
