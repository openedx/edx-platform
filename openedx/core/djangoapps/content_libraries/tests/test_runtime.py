# -*- coding: utf-8 -*-
"""
Test the Blockstore-based XBlock runtime and content libraries together.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import unittest

from django.conf import settings
from django.test import TestCase
from organizations.models import Organization
from xblock.core import XBlock, Scope
from xblock import fields

from openedx.core.djangoapps.content_libraries import api as library_api
from openedx.core.djangoapps.xblock import api as xblock_api
from openedx.core.lib import blockstore_api
from student.tests.factories import UserFactory
from xmodule.unit_block import UnitBlock


class UserStateTestBlock(XBlock):
    """
    Block for testing variously scoped XBlock fields.
    """
    BLOCK_TYPE = "user-state-test"

    display_name = fields.String(scope=Scope.content, name='User State Test Block')
    # User-specific fields:
    user_str = fields.String(scope=Scope.user_state, default='default value')  # This usage, one user
    uss_str = fields.String(scope=Scope.user_state_summary, default='default value')  # This usage, all users
    pref_str = fields.String(scope=Scope.preferences, default='default value')  # Block type, one user
    user_info_str = fields.String(scope=Scope.user_info, default='default value')  # All blocks, one user


class ContentLibraryContentTestMixin(object):
    """
    Mixin for content library tests that creates two students and a library.
    """
    @classmethod
    def setUpClass(cls):
        super(ContentLibraryContentTestMixin, cls).setUpClass()
        # Create a couple students that the tests can use
        cls.student_a = UserFactory.create(username="Alice", email="alice@example.com")
        cls.student_b = UserFactory.create(username="Bob", email="bob@example.com")
        # Create a collection using Blockstore API directly only because there
        # is not yet any Studio REST API for doing so:
        cls.collection = blockstore_api.create_collection("Content Library Test Collection")
        # Create an organization
        cls.organization = Organization.objects.create(
            name="Content Libraries Tachyon Exploration & Survey Team",
            short_name="CL-TEST",
        )
        cls.library = library_api.create_library(
            collection_uuid=cls.collection.uuid,
            org=cls.organization,
            slug=cls.__name__,
            title=(cls.__name__ + " Test Lib"),
            description="",
        )


@unittest.skipUnless(settings.RUN_BLOCKSTORE_TESTS, "Requires a running Blockstore server")
class ContentLibraryRuntimeTest(ContentLibraryContentTestMixin, TestCase):
    """
    Basic tests of the Blockstore-based XBlock runtime using XBlocks in a
    content library.
    """

    def test_has_score(self):
        """
        Test that the LMS-specific 'has_score' attribute is getting added to
        blocks.
        """
        unit_block_key = library_api.create_library_block(self.library.key, "unit", "u1").usage_key
        problem_block_key = library_api.create_library_block(self.library.key, "problem", "p1").usage_key
        library_api.publish_changes(self.library.key)
        unit_block = xblock_api.load_block(unit_block_key, self.student_a)
        problem_block = xblock_api.load_block(problem_block_key, self.student_a)

        self.assertFalse(hasattr(UnitBlock, 'has_score'))  # The block class doesn't declare 'has_score'
        self.assertEqual(unit_block.has_score, False)  # But it gets added by the runtime and defaults to False
        # And problems do have has_score True:
        self.assertEqual(problem_block.has_score, True)


@unittest.skipUnless(settings.RUN_BLOCKSTORE_TESTS, "Requires a running Blockstore server")
# We can remove the line below to enable this in Studio once we implement a session-backed
# field data store which we can use for both studio users and anonymous users
@unittest.skipUnless(settings.ROOT_URLCONF == "lms.urls", "Student State is only saved in the LMS")
class ContentLibraryXBlockUserStateTest(ContentLibraryContentTestMixin, TestCase):
    """
    Test that the Blockstore-based XBlock runtime can store and retrieve student
    state for XBlocks when learners access blocks directly in a library context,
    if the library allows direct learning.
    """

    @XBlock.register_temp_plugin(UserStateTestBlock, UserStateTestBlock.BLOCK_TYPE)
    def test_default_values(self):
        """
        Test that a user sees the default field values at first
        """
        block_metadata = library_api.create_library_block(self.library.key, UserStateTestBlock.BLOCK_TYPE, "b1")
        block_usage_key = block_metadata.usage_key
        library_api.publish_changes(self.library.key)

        block_alice = xblock_api.load_block(block_usage_key, self.student_a)

        self.assertEqual(block_alice.scope_ids.user_id, self.student_a.id)
        self.assertEqual(block_alice.user_str, 'default value')
        self.assertEqual(block_alice.uss_str, 'default value')
        self.assertEqual(block_alice.pref_str, 'default value')
        self.assertEqual(block_alice.user_info_str, 'default value')

    @XBlock.register_temp_plugin(UserStateTestBlock, UserStateTestBlock.BLOCK_TYPE)
    def test_modify_state_directly(self):
        """
        Test that we can modify user-specific XBlock fields directly in Python
        """
        # Create two XBlocks, block1 and block2
        block1_metadata = library_api.create_library_block(self.library.key, UserStateTestBlock.BLOCK_TYPE, "b2-1")
        block1_usage_key = block1_metadata.usage_key
        block2_metadata = library_api.create_library_block(self.library.key, UserStateTestBlock.BLOCK_TYPE, "b2-2")
        block2_usage_key = block2_metadata.usage_key
        library_api.publish_changes(self.library.key)

        # Alice changes all the fields of block1:
        block1_alice = xblock_api.load_block(block1_usage_key, self.student_a)
        block1_alice.user_str = 'Alice was here'
        block1_alice.uss_str = 'Alice was here (USS)'
        block1_alice.pref_str = 'Alice was here (prefs)'
        block1_alice.user_info_str = 'Alice was here (user info)'
        block1_alice.save()

        # Now load it back and expect the same field data:
        block1_alice = xblock_api.load_block(block1_usage_key, self.student_a)

        self.assertEqual(block1_alice.scope_ids.user_id, self.student_a.id)
        self.assertEqual(block1_alice.user_str, 'Alice was here')
        self.assertEqual(block1_alice.uss_str, 'Alice was here (USS)')
        self.assertEqual(block1_alice.pref_str, 'Alice was here (prefs)')
        self.assertEqual(block1_alice.user_info_str, 'Alice was here (user info)')

        # Now load a different block for Alice:
        block2_alice = xblock_api.load_block(block2_usage_key, self.student_a)
        # User state should be default:
        self.assertEqual(block2_alice.user_str, 'default value')
        # User state summary should be default:
        self.assertEqual(block2_alice.uss_str, 'default value')
        # But prefs and user info should be shared:
        self.assertEqual(block2_alice.pref_str, 'Alice was here (prefs)')
        self.assertEqual(block2_alice.user_info_str, 'Alice was here (user info)')

        # Now load the first block, block1, for Bob:
        block1_bob = xblock_api.load_block(block1_usage_key, self.student_b)

        self.assertEqual(block1_bob.scope_ids.user_id, self.student_b.id)
        self.assertEqual(block1_bob.user_str, 'default value')
        self.assertEqual(block1_bob.uss_str, 'Alice was here (USS)')
        self.assertEqual(block1_bob.pref_str, 'default value')
        self.assertEqual(block1_bob.user_info_str, 'default value')

    @XBlock.register_temp_plugin(UserStateTestBlock, UserStateTestBlock.BLOCK_TYPE)
    def test_independent_instances(self):
        """
        Test that independent instances of the same block don't share field data
        until .save() and re-loading, even when they're using the same runtime.
        """
        block_metadata = library_api.create_library_block(self.library.key, UserStateTestBlock.BLOCK_TYPE, "b3")
        block_usage_key = block_metadata.usage_key
        library_api.publish_changes(self.library.key)

        block_instance1 = xblock_api.load_block(block_usage_key, self.student_a)
        block_instance2 = block_instance1.runtime.get_block(block_usage_key)

        # We could assert that both instances of the block have the same runtime
        # instance, but that's an implementation detail. The main point of this
        # test is just to make sure there's never any surprises when reading
        # field data out of an XBlock, because of other instances of the same
        # block.

        block_instance1.user_str = 'changed to this'
        self.assertNotEqual(block_instance1.user_str, block_instance2.user_str)

        block_instance1.save()
        self.assertNotEqual(block_instance1.user_str, block_instance2.user_str)

        block_instance2 = block_instance1.runtime.get_block(block_usage_key)
        # Now they should be equal, because we've saved and re-loaded instance2:
        self.assertEqual(block_instance1.user_str, block_instance2.user_str)
