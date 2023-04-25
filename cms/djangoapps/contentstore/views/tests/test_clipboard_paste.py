"""
Test the import_staged_content_from_user_clipboard() method, which is used to
allow users to paste XBlocks that were copied using the staged_content/clipboard
APIs.
"""
from opaque_keys.edx.keys import UsageKey
from rest_framework.test import APIClient
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory

CLIPBOARD_ENDPOINT = "/api/content-staging/v1/clipboard/"
XBLOCK_ENDPOINT = "/xblock/"


class ClipboardPasteTestCase(ModuleStoreTestCase):
    """
    Test Clipboard Paste functionality
    """

    def _setup_course(self):
        """ Set up the "Toy Course" and an APIClient for testing clipboard functionality. """
        # Setup:
        course_key = ToyCourseFactory.create().id  # See xmodule/modulestore/tests/sample_courses.py
        client = APIClient()
        client.login(username=self.user.username, password=self.user_password)
        return (course_key, client)

    def test_copy_and_paste_video(self):
        """
        Test copying a video from the course, and pasting it into the same unit
        """
        course_key, client = self._setup_course()

        # Check how many blocks are in the vertical currently
        parent_key = course_key.make_usage_key("vertical", "vertical_test")  # This is the vertical that holds the video
        orig_vertical = modulestore().get_item(parent_key)
        assert len(orig_vertical.children) == 4

        # Copy the video
        video_key = course_key.make_usage_key("video", "sample_video")
        copy_response = client.post(CLIPBOARD_ENDPOINT, {"usage_key": str(video_key)}, format="json")
        assert copy_response.status_code == 200

        # Paste the video
        paste_response = client.post(XBLOCK_ENDPOINT, {
            "parent_locator": str(parent_key),
            "staged_content": "clipboard",
        }, format="json")
        assert paste_response.status_code == 200
        new_block_key = UsageKey.from_string(paste_response.json()["locator"])

        # Now there should be an extra block in the vertical:
        updated_vertical = modulestore().get_item(parent_key)
        assert len(updated_vertical.children) == 5
        assert updated_vertical.children[-1] == new_block_key
        # And it should match the original:
        orig_video = modulestore().get_item(video_key)
        new_video = modulestore().get_item(new_block_key)
        assert new_video.youtube_id_1_0 == orig_video.youtube_id_1_0
        # The new block should store a reference to where it was copied from
        assert new_video.copied_from_block == str(video_key)
