"""
Test the Blockstore-based XBlock runtime and content libraries together.
"""
import json
from gettext import GNUTranslations

from completion.test_utils import CompletionWaffleTestMixin
from django.db import connections, transaction
from django.test import LiveServerTestCase, TestCase
from django.utils.text import slugify
from organizations.models import Organization
from rest_framework.test import APIClient
from xblock.core import XBlock

from lms.djangoapps.courseware.model_data import get_score
from openedx.core.djangoapps.content_libraries import api as library_api
from openedx.core.djangoapps.content_libraries.tests.base import (
    BlockstoreAppTestMixin,
    requires_blockstore,
    requires_blockstore_app,
    URL_BLOCK_RENDER_VIEW,
    URL_BLOCK_GET_HANDLER_URL,
    URL_BLOCK_METADATA_URL,
)
from openedx.core.djangoapps.content_libraries.tests.user_state_block import UserStateTestBlock
from openedx.core.djangoapps.content_libraries.constants import COMPLEX, ALL_RIGHTS_RESERVED, CC_4_BY
from openedx.core.djangoapps.dark_lang.models import DarkLangConfig
from openedx.core.djangoapps.xblock import api as xblock_api
from openedx.core.djangolib.testing.utils import skip_unless_lms, skip_unless_cms
from openedx.core.lib import blockstore_api
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.unit_block import UnitBlock  # lint-amnesty, pylint: disable=wrong-import-order


class ContentLibraryContentTestMixin:
    """
    Mixin for content library tests that creates two students and a library.
    """
    def setUp(self):
        super().setUp()
        # Create a couple students that the tests can use
        self.student_a = UserFactory.create(username="Alice", email="alice@example.com", password="edx")
        self.student_b = UserFactory.create(username="Bob", email="bob@example.com", password="edx")

        # Create a collection using Blockstore API directly only because there
        # is not yet any Studio REST API for doing so:
        self.collection = blockstore_api.create_collection("Content Library Test Collection")
        # Create an organization
        self.organization = Organization.objects.create(
            name="Content Libraries Tachyon Exploration & Survey Team",
            short_name="CL-TEST",
        )
        _, slug = self.id().rsplit('.', 1)
        with transaction.atomic():
            self.library = library_api.create_library(
                collection_uuid=self.collection.uuid,
                library_type=COMPLEX,
                org=self.organization,
                slug=slugify(slug),
                title=(f"{slug} Test Lib"),
                description="",
                allow_public_learning=True,
                allow_public_read=False,
                library_license=ALL_RIGHTS_RESERVED,
            )


class ContentLibraryRuntimeTestMixin(ContentLibraryContentTestMixin):
    """
    Basic tests of the Blockstore-based XBlock runtime using XBlocks in a
    content library.
    """

    @skip_unless_cms  # creating child blocks only works properly in Studio
    def test_identical_olx(self):
        """
        Test library blocks with children that also have identical OLX. Since
        the blockstore runtime caches authored field data based on the hash of
        the OLX, this can catch some potential bugs, especially given that the
        "children" field stores usage IDs, not definition IDs.
        """
        # Create a unit containing a <problem>
        unit_block_key = library_api.create_library_block(self.library.key, "unit", "u1").usage_key
        library_api.create_library_block_child(unit_block_key, "problem", "p1")
        library_api.publish_changes(self.library.key)
        # Now do the same in a different library:
        with transaction.atomic():
            library2 = library_api.create_library(
                collection_uuid=self.collection.uuid,
                org=self.organization,
                slug="idolx",
                title=("Identical OLX Test Lib 2"),
                description="",
                library_type=COMPLEX,
                allow_public_learning=True,
                allow_public_read=False,
                library_license=CC_4_BY,
            )
        unit_block2_key = library_api.create_library_block(library2.key, "unit", "u1").usage_key
        library_api.create_library_block_child(unit_block2_key, "problem", "p1")
        library_api.publish_changes(library2.key)
        # Load both blocks:
        unit_block = xblock_api.load_block(unit_block_key, self.student_a)
        unit_block2 = xblock_api.load_block(unit_block2_key, self.student_a)
        assert library_api.get_library_block_olx(unit_block_key) == library_api.get_library_block_olx(unit_block2_key)
        assert unit_block.children != unit_block2.children

    def test_dndv2_sets_translator(self):
        dnd_block_key = library_api.create_library_block(self.library.key, "drag-and-drop-v2", "dnd1").usage_key
        library_api.publish_changes(self.library.key)
        dnd_block = xblock_api.load_block(dnd_block_key, self.student_a)
        i18n_service = dnd_block.runtime.service(dnd_block, 'i18n')
        assert isinstance(i18n_service.translator, GNUTranslations)

    def test_has_score(self):
        """
        Test that the LMS-specific 'has_score' attribute is getting added to
        blocks.
        """
        unit_block_key = library_api.create_library_block(self.library.key, "unit", "score-unit1").usage_key
        problem_block_key = library_api.create_library_block(self.library.key, "problem", "score-prob1").usage_key
        library_api.publish_changes(self.library.key)
        unit_block = xblock_api.load_block(unit_block_key, self.student_a)
        problem_block = xblock_api.load_block(problem_block_key, self.student_a)

        assert not hasattr(UnitBlock, 'has_score')
        # The block class doesn't declare 'has_score'
        assert unit_block.has_score is False
        # But it gets added by the runtime and defaults to False
        # And problems do have has_score True:
        assert problem_block.has_score is True

    @skip_unless_cms  # creating child blocks only works properly in Studio
    def test_xblock_metadata(self):
        """
        Test the XBlock metadata API
        """
        unit_block_key = library_api.create_library_block(self.library.key, "unit", "metadata-u1").usage_key
        problem_key = library_api.create_library_block_child(unit_block_key, "problem", "metadata-p1").usage_key
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
        library_api.set_library_block_olx(problem_key, new_olx)
        library_api.publish_changes(self.library.key)

        # Now view the problem as Alice:
        client = APIClient()
        client.login(username=self.student_a.username, password='edx')

        # Check the metadata API for the unit:
        metadata_view_result = client.get(
            URL_BLOCK_METADATA_URL.format(block_key=unit_block_key),
            {"include": "children,editable_children"},
        )
        assert metadata_view_result.data['children'] == [str(problem_key)]
        assert metadata_view_result.data['editable_children'] == [str(problem_key)]

        # Check the metadata API for the problem:
        metadata_view_result = client.get(
            URL_BLOCK_METADATA_URL.format(block_key=problem_key),
            {"include": "student_view_data,index_dictionary"},
        )
        assert metadata_view_result.data['block_id'] == str(problem_key)
        assert metadata_view_result.data['display_name'] == 'New Multi Choice Question'
        assert 'children' not in metadata_view_result.data
        assert 'editable_children' not in metadata_view_result.data
        self.assertDictContainsSubset({
            "content_type": "CAPA",
            "problem_types": ["multiplechoiceresponse"],
        }, metadata_view_result.data["index_dictionary"])
        assert metadata_view_result.data['student_view_data'] is None
        # Capa doesn't provide student_view_data


@requires_blockstore
class ContentLibraryRuntimeBServiceTest(ContentLibraryRuntimeTestMixin, TestCase):
    """
    Tests XBlock runtime using XBlocks in a content library using the standalone Blockstore service.
    """


@requires_blockstore_app
class ContentLibraryRuntimeTest(ContentLibraryRuntimeTestMixin, BlockstoreAppTestMixin, LiveServerTestCase):
    """
    Tests XBlock runtime using XBlocks in a content library using the installed Blockstore app.

    We run this test with a live server, so that the blockstore asset files can be served.
    """


# We can remove the line below to enable this in Studio once we implement a session-backed
# field data store which we can use for both studio users and anonymous users
@skip_unless_lms
class ContentLibraryXBlockUserStateTestMixin(ContentLibraryContentTestMixin):
    """
    Test that the Blockstore-based XBlock runtime can store and retrieve student
    state for XBlocks when learners access blocks directly in a library context,
    if the library allows direct learning.
    """

    databases = set(connections)

    @XBlock.register_temp_plugin(UserStateTestBlock, UserStateTestBlock.BLOCK_TYPE)
    def test_default_values(self):
        """
        Test that a user sees the default field values at first
        """
        block_metadata = library_api.create_library_block(self.library.key, UserStateTestBlock.BLOCK_TYPE, "b1")
        block_usage_key = block_metadata.usage_key
        library_api.publish_changes(self.library.key)

        block_alice = xblock_api.load_block(block_usage_key, self.student_a)

        assert block_alice.scope_ids.user_id == self.student_a.id
        assert block_alice.user_str == 'default value'
        assert block_alice.uss_str == 'default value'
        assert block_alice.pref_str == 'default value'
        assert block_alice.user_info_str == 'default value'

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

        assert block1_alice.scope_ids.user_id == self.student_a.id
        assert block1_alice.user_str == 'Alice was here'
        assert block1_alice.uss_str == 'Alice was here (USS)'
        assert block1_alice.pref_str == 'Alice was here (prefs)'
        assert block1_alice.user_info_str == 'Alice was here (user info)'

        # Now load a different block for Alice:
        block2_alice = xblock_api.load_block(block2_usage_key, self.student_a)
        # User state should be default:
        assert block2_alice.user_str == 'default value'
        # User state summary should be default:
        assert block2_alice.uss_str == 'default value'
        # But prefs and user info should be shared:
        assert block2_alice.pref_str == 'Alice was here (prefs)'
        assert block2_alice.user_info_str == 'Alice was here (user info)'

        # Now load the first block, block1, for Bob:
        block1_bob = xblock_api.load_block(block1_usage_key, self.student_b)

        assert block1_bob.scope_ids.user_id == self.student_b.id
        assert block1_bob.user_str == 'default value'
        assert block1_bob.uss_str == 'Alice was here (USS)'
        assert block1_bob.pref_str == 'default value'
        assert block1_bob.user_info_str == 'default value'

    @XBlock.register_temp_plugin(UserStateTestBlock, UserStateTestBlock.BLOCK_TYPE)
    def test_state_for_anonymous_users(self):
        """
        Test that anonymous users can interact with XBlocks and get/set their
        state via handlers.
        """
        # Create two XBlocks, block1 and block2
        block1_metadata = library_api.create_library_block(self.library.key, UserStateTestBlock.BLOCK_TYPE, "b3-1")
        block1_usage_key = block1_metadata.usage_key
        block2_metadata = library_api.create_library_block(self.library.key, UserStateTestBlock.BLOCK_TYPE, "b3-2")
        block2_usage_key = block2_metadata.usage_key
        library_api.publish_changes(self.library.key)
        # Create two clients (anonymous user's browsers)
        client1 = APIClient()
        client2 = APIClient()

        def call_handler(client, block_key, handler_name, method, data=None):
            """ Call an XBlock handler """
            url_result = client.get(URL_BLOCK_GET_HANDLER_URL.format(block_key=block_key, handler_name=handler_name))
            url = url_result.data["handler_url"]
            data_json = json.dumps(data) if data else None
            response = getattr(client, method)(url, data_json, content_type="application/json")
            assert response.status_code == 200
            return response.json()

        # Now client1 sets all the fields via a handler:
        call_handler(client1, block1_usage_key, "set_user_state", "post", {
            "user_str": "1 was here",
            "uss_str": "1 was here (USS)",
            "pref_str": "1 was here (prefs)",
            "user_info_str": "1 was here (user info)",
        })

        # Now load it back and expect the same data:
        data = call_handler(client1, block1_usage_key, "get_user_state", "get")
        assert data['user_str'] == '1 was here'
        assert data['uss_str'] == '1 was here (USS)'
        assert data['pref_str'] == '1 was here (prefs)'
        assert data['user_info_str'] == '1 was here (user info)'

        # Now load a different XBlock and expect only pref_str and user_info_str to be set:
        data = call_handler(client1, block2_usage_key, "get_user_state", "get")
        assert data['user_str'] == 'default value'
        assert data['uss_str'] == 'default value'
        assert data['pref_str'] == '1 was here (prefs)'
        assert data['user_info_str'] == '1 was here (user info)'

        # Now a different anonymous user loading the first block should see only the uss_str set:
        data = call_handler(client2, block1_usage_key, "get_user_state", "get")
        assert data['user_str'] == 'default value'
        assert data['uss_str'] == '1 was here (USS)'
        assert data['pref_str'] == 'default value'
        assert data['user_info_str'] == 'default value'

        # The "user state summary" should not be shared between registered and anonymous users:
        client_registered = APIClient()
        client_registered.login(username=self.student_a.username, password='edx')
        data = call_handler(client_registered, block1_usage_key, "get_user_state", "get")
        assert data['user_str'] == 'default value'
        assert data['uss_str'] == 'default value'
        assert data['pref_str'] == 'default value'
        assert data['user_info_str'] == 'default value'

    def test_views_for_anonymous_users(self):
        """
        Test that anonymous users can view XBlock's 'public_view' but not other
        views
        """
        # Create an XBlock
        block_metadata = library_api.create_library_block(self.library.key, "html", "html1")
        block_usage_key = block_metadata.usage_key
        library_api.set_library_block_olx(block_usage_key, "<html>Hello world</html>")
        library_api.publish_changes(self.library.key)

        anon_client = APIClient()
        # View the public_view:
        public_view_result = anon_client.get(
            URL_BLOCK_RENDER_VIEW.format(block_key=block_usage_key, view_name='public_view'),
        )
        assert public_view_result.status_code == 200
        assert 'Hello world' in public_view_result.data['content']

        # Try to view the student_view:
        public_view_result = anon_client.get(
            URL_BLOCK_RENDER_VIEW.format(block_key=block_usage_key, view_name='student_view'),
        )
        assert public_view_result.status_code == 403

    @XBlock.register_temp_plugin(UserStateTestBlock, UserStateTestBlock.BLOCK_TYPE)
    def test_independent_instances(self):
        """
        Test that independent instances of the same block don't share field data
        until .save() and re-loading, even when they're using the same runtime.
        """
        block_metadata = library_api.create_library_block(self.library.key, UserStateTestBlock.BLOCK_TYPE, "b4")
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
        assert block_instance1.user_str != block_instance2.user_str

        block_instance1.save()
        assert block_instance1.user_str != block_instance2.user_str

        block_instance2 = block_instance1.runtime.get_block(block_usage_key)
        # Now they should be equal, because we've saved and re-loaded instance2:
        assert block_instance1.user_str == block_instance2.user_str

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
        problem_key = f"input_{block_id}_2_1"
        assert problem_key in student_view_result.data['content']

        # And submit a wrong answer:
        result = client.get(URL_BLOCK_GET_HANDLER_URL.format(block_key=block_id, handler_name='xmodule_handler'))
        problem_check_url = result.data["handler_url"] + 'problem_check'

        submit_result = client.post(problem_check_url, data={problem_key: "choice_3"})
        assert submit_result.status_code == 200
        submit_data = json.loads(submit_result.content.decode('utf-8'))
        self.assertDictContainsSubset({
            "current_score": 0,
            "total_possible": 1,
            "attempts_used": 1,
        }, submit_data)

        # Now test that the score is also persisted in StudentModule:
        # If we add a REST API to get an individual block's score, that should be checked instead of StudentModule.
        sm = get_score(self.student_a, block_id)
        assert sm.grade == 0
        assert sm.max_grade == 1

        # And submit a correct answer:
        submit_result = client.post(problem_check_url, data={problem_key: "choice_1"})
        assert submit_result.status_code == 200
        submit_data = json.loads(submit_result.content.decode('utf-8'))
        self.assertDictContainsSubset({
            "current_score": 1,
            "total_possible": 1,
            "attempts_used": 2,
        }, submit_data)
        # Now test that the score is also updated in StudentModule:
        # If we add a REST API to get an individual block's score, that should be checked instead of StudentModule.
        sm = get_score(self.student_a, block_id)
        assert sm.grade == 1
        assert sm.max_grade == 1

    @skip_unless_lms
    def test_i18n(self):
        """
        Test that a block's rendered content respects the Accept-Language header and returns translated content.
        """
        block_id = library_api.create_library_block(self.library.key, "problem", "i18n_problem").usage_key
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

        # Enable the dummy language in darklang
        DarkLangConfig(
            released_languages='eo',
            changed_by=self.student_a,
            enabled=True
        ).save()

        client = APIClient()

        # View the problem without specifying a language
        default_public_view = client.get(URL_BLOCK_RENDER_VIEW.format(block_key=block_id, view_name='public_view'))
        assert 'Submit' in default_public_view.data['content']
        assert 'Süßmït' not in default_public_view.data['content']

        # View the problem and request the dummy language
        dummy_public_view = client.get(URL_BLOCK_RENDER_VIEW.format(block_key=block_id, view_name='public_view'),
                                       HTTP_ACCEPT_LANGUAGE='eo')
        assert 'Süßmït' in dummy_public_view.data['content']
        assert 'Submit' not in dummy_public_view.data['content']


@requires_blockstore
class ContentLibraryXBlockUserStateBServiceTest(ContentLibraryXBlockUserStateTestMixin, TestCase):
    """
    Tests XBlock user state for XBlocks in a content library using the standalone Blockstore service.
    """


@requires_blockstore_app
class ContentLibraryXBlockUserStateTest(
    ContentLibraryXBlockUserStateTestMixin,
    BlockstoreAppTestMixin,
    LiveServerTestCase,
):
    """
    Tests XBlock user state for XBlocks in a content library using the installed Blockstore app.

    We run this test with a live server, so that the blockstore asset files can be served.
    """


@skip_unless_lms  # No completion tracking in Studio
class ContentLibraryXBlockCompletionTestMixin(ContentLibraryContentTestMixin, CompletionWaffleTestMixin):
    """
    Test that the Blockstore-based XBlocks can track their completion status
    using the completion library.
    """

    def setUp(self):
        super().setUp()
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
        assert get_block_completion_status() == 0

        # Now call the 'publish_completion' handler:
        client = APIClient()
        client.login(username=self.student_a.username, password='edx')
        result = client.get(URL_BLOCK_GET_HANDLER_URL.format(block_key=block_id, handler_name='publish_completion'))
        publish_completion_url = result.data["handler_url"]

        # This will test the 'completion' service and the completion event handler:
        result2 = client.post(publish_completion_url, {"completion": 1.0}, format='json')
        assert result2.status_code == 200

        # Now the block is completed
        assert get_block_completion_status() == 1


@requires_blockstore
class ContentLibraryXBlockCompletionBServiceTest(
    ContentLibraryXBlockCompletionTestMixin,
    CompletionWaffleTestMixin,
    TestCase,
):
    """
    Test that the Blockstore-based XBlocks can track their completion status
    using the standalone Blockstore service.
    """


@requires_blockstore_app
class ContentLibraryXBlockCompletionTest(
    ContentLibraryXBlockCompletionTestMixin,
    CompletionWaffleTestMixin,
    BlockstoreAppTestMixin,
    LiveServerTestCase,
):
    """
    Test that the Blockstore-based XBlocks can track their completion status
    using the installed Blockstore app.

    We run this test with a live server, so that the blockstore asset files can be served.
    """
