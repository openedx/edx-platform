"""
Test the import_staged_content_from_user_clipboard() method, which is used to
allow users to paste XBlocks that were copied using the staged_content/clipboard
APIs.
"""
from opaque_keys.edx.keys import UsageKey
from rest_framework.test import APIClient
from xmodule.modulestore.django import contentstore, modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, upload_file_to_course
from xmodule.modulestore.tests.factories import BlockFactory, CourseFactory, ToyCourseFactory

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

    def test_paste_with_assets(self):
        """
        When pasting into a different course, any required static assets should
        be pasted too, unless they already exist in the destination course.
        """
        dest_course_key, client = self._setup_course()
        # Make sure some files exist in the source course to be copied:
        source_course = CourseFactory.create()
        upload_file_to_course(
            course_key=source_course.id,
            contentstore=contentstore(),
            source_file='./common/test/data/static/picture1.jpg',
            target_filename="picture1.jpg",
        )
        upload_file_to_course(
            course_key=source_course.id,
            contentstore=contentstore(),
            source_file='./common/test/data/static/picture2.jpg',
            target_filename="picture2.jpg",
        )
        source_html = BlockFactory.create(
            parent_location=source_course.location,
            category="html",
            display_name="Some HTML",
            data="""
            <p>
                <a href="/static/picture1.jpg">Picture 1</a>
                <a href="/static/picture2.jpg">Picture 2</a>
            </p>
            """,
        )

        # Now, to test conflict handling, we also upload a CONFLICTING image to
        # the destination course under the same filename.
        upload_file_to_course(
            course_key=dest_course_key,
            contentstore=contentstore(),
            # Note this is picture 3, not picture 2, but we save it as picture 2:
            source_file='./common/test/data/static/picture3.jpg',
            target_filename="picture2.jpg",
        )

        # Now copy the HTML block from the source cost and paste it into the destination:
        copy_response = client.post(CLIPBOARD_ENDPOINT, {"usage_key": str(source_html.location)}, format="json")
        assert copy_response.status_code == 200

        # Paste the video
        dest_parent_key = dest_course_key.make_usage_key("vertical", "vertical_test")
        paste_response = client.post(XBLOCK_ENDPOINT, {
            "parent_locator": str(dest_parent_key),
            "staged_content": "clipboard",
        }, format="json")
        assert paste_response.status_code == 200
        static_file_notices = paste_response.json()["static_file_notices"]
        assert static_file_notices == {
            "error_files": [],
            "new_files": ["picture1.jpg"],
            # The new course already had a file named "picture2.jpg" with different md5 hash, so it's a conflict:
            "conflicting_files": ["picture2.jpg"],
        }

        # Check that the files are as we expect:
        source_pic1_hash = contentstore().find(source_course.id.make_asset_key("asset", "picture1.jpg")).content_digest
        dest_pic1_hash = contentstore().find(dest_course_key.make_asset_key("asset", "picture1.jpg")).content_digest
        assert source_pic1_hash == dest_pic1_hash
        source_pic2_hash = contentstore().find(source_course.id.make_asset_key("asset", "picture2.jpg")).content_digest
        dest_pic2_hash = contentstore().find(dest_course_key.make_asset_key("asset", "picture2.jpg")).content_digest
        assert source_pic2_hash != dest_pic2_hash  # Because there was a conflict, this file was unchanged.
