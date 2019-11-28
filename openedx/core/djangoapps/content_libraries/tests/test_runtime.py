# -*- coding: utf-8 -*-
"""
Test the Blockstore-based XBlock runtime and content libraries together.
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import json
import unittest

from completion.test_utils import CompletionWaffleTestMixin
from django.test import TestCase
from organizations.models import Organization
from rest_framework.test import APIClient
from xblock.core import XBlock, Scope
from xblock import fields

from lms.djangoapps.courseware.model_data import get_score
from openedx.core.djangoapps.content_libraries import api as library_api
from openedx.core.djangoapps.content_libraries.tests.base import (
    requires_blockstore,
    URL_BLOCK_RENDER_VIEW,
    URL_BLOCK_GET_HANDLER_URL,
)
from openedx.core.djangoapps.xblock import api as xblock_api
from openedx.core.djangolib.testing.utils import skip_unless_lms
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
        cls.student_a = UserFactory.create(username="Alice", email="alice@example.com", password="edx")
        cls.student_b = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
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


@requires_blockstore
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


@requires_blockstore
# We can remove the line below to enable this in Studio once we implement a session-backed
# field data store which we can use for both studio users and anonymous users
@skip_unless_lms
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

    @skip_unless_lms  # Scores are only used in the LMS
    def test_scores_persisted(self):
        """
        Test that a block's emitted scores are cached in StudentModule

        In the future if there is a REST API to retrieve individual block's
        scores, that should be used instead of checking StudentModule directly.
        """
        block_id = library_api.create_library_block(self.library.key, "problem", "scored_problem").usage_key
        new_olx = """
        <problem display_name="New Multi Choice Question" max_attempts="5">
            <multiplechoiceresponse>
                <p>This is a normal capa problem. It has "maximum attempts" set to **5**.</p>
                <label>Blockstore is designed to store.</label>
                <choicegroup type="MultipleChoice">
                    <choice correct="false">XBlock metadata only</choice>
                    <choice correct="true">XBlock data/metadata and associated static asset files</choice>
                    <choice correct="false">Static asset files for XBlocks and courseware</choice>
                    <choice correct="false">XModule metadata only</choice>
                </choicegroup>
            </multiplechoiceresponse>
        </problem>
        """.strip()
        library_api.set_library_block_olx(block_id, new_olx)
        library_api.publish_changes(self.library.key)

        # Now view the problem as Alice:
        client = APIClient()
        client.login(username=self.student_a.username, password='edx')
        student_view_result = client.get(URL_BLOCK_RENDER_VIEW.format(block_key=block_id, view_name='student_view'))
        problem_key = "input_{}_2_1".format(block_id)
        self.assertIn(problem_key, student_view_result.data["content"])
        # And submit a wrong answer:
        result = client.get(URL_BLOCK_GET_HANDLER_URL.format(block_key=block_id, handler_name='xmodule_handler'))
        problem_check_url = result.data["handler_url"] + 'problem_check'

        submit_result = client.post(problem_check_url, data={problem_key: "choice_3"})
        self.assertEqual(submit_result.status_code, 200)
        submit_data = json.loads(submit_result.content)
        self.assertDictContainsSubset({
            "current_score": 0,
            "total_possible": 1,
            "attempts_used": 1,
        }, submit_data)

        # Now test that the score is also persisted in StudentModule:
        # If we add a REST API to get an individual block's score, that should be checked instead of StudentModule.
        sm = get_score(self.student_a, block_id)
        self.assertEqual(sm.grade, 0)
        self.assertEqual(sm.max_grade, 1)

        # And submit a correct answer:
        submit_result = client.post(problem_check_url, data={problem_key: "choice_1"})
        self.assertEqual(submit_result.status_code, 200)
        submit_data = json.loads(submit_result.content)
        self.assertDictContainsSubset({
            "current_score": 1,
            "total_possible": 1,
            "attempts_used": 2,
        }, submit_data)
        # Now test that the score is also updated in StudentModule:
        # If we add a REST API to get an individual block's score, that should be checked instead of StudentModule.
        sm = get_score(self.student_a, block_id)
        self.assertEqual(sm.grade, 1)
        self.assertEqual(sm.max_grade, 1)


@requires_blockstore
@skip_unless_lms  # No completion tracking in Studio
class ContentLibraryXBlockCompletionTest(ContentLibraryContentTestMixin, CompletionWaffleTestMixin, TestCase):
    """
    Test that the Blockstore-based XBlocks can track their completion status
    using the completion library.
    """

    def setUp(self):
        super(ContentLibraryXBlockCompletionTest, self).setUp()
        # Enable the completion waffle flag for these tests
        self.override_waffle_switch(True)

    def test_mark_complete_via_handler(self):
        """
        Test that a "complete on view" XBlock like the HTML block can be marked
        as complete using the LmsBlockMixin.publish_completion handler.
        """
        block_id = library_api.create_library_block(self.library.key, "html", "completable_html").usage_key
        new_olx = """
        <html display_name="Read this HTML">
            <![CDATA[
                <p>This is some <strong>HTML</strong>.</p>
            ]]>
        </html>
        """.strip()
        library_api.set_library_block_olx(block_id, new_olx)
        library_api.publish_changes(self.library.key)

        # We should get a REST API for retrieving completion data; for now use python

        def get_block_completion_status():
            """ Get block completion status (0 to 1) """
            block = xblock_api.load_block(block_id, self.student_a)
            assert hasattr(block, 'publish_completion')
            service = block.runtime.service(block, 'completion')
            return service.get_completions([block_id])[block_id]

        # At first the block is not completed
        self.assertEqual(get_block_completion_status(), 0)

        # Now call the 'publish_completion' handler:
        client = APIClient()
        client.login(username=self.student_a.username, password='edx')
        result = client.get(URL_BLOCK_GET_HANDLER_URL.format(block_key=block_id, handler_name='publish_completion'))
        publish_completion_url = result.data["handler_url"]

        # This will test the 'completion' service and the completion event handler:
        result2 = client.post(publish_completion_url, {"completion": 1.0}, format='json')
        self.assertEqual(result2.status_code, 200)

        # Now the block is completed
        self.assertEqual(get_block_completion_status(), 1)
