# -*- coding: utf-8 -*-
"""
Tests for static asset files in Blockstore-based Content Libraries
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import requests

from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest

# Binary data representing an SVG image file
SVG_DATA = """<svg xmlns="http://www.w3.org/2000/svg" height="30" width="100">
  <text x="0" y="15" fill="red">SVG is 🔥</text>
</svg>""".encode('utf-8')


class ContentLibrariesStaticAssetsTest(ContentLibrariesRestApiTest):
    """
    Tests for static asset files in Blockstore-based Content Libraries

    WARNING: every test should have a unique library slug, because even though
    the django/mysql database gets reset for each test case, the lookup between
    library slug and bundle UUID does not because it's assumed to be immutable
    and cached forever.
    """

    def test_asset_crud(self):
        """
        Test create, read, update, and write of a static asset file.

        Also tests that the static asset file (an image in this case) can be
        used in an HTML block.
        """
        library = self._create_library(slug="asset-lib1", title="Static Assets Test Library")
        block = self._add_block_to_library(library["id"], "html", "html1")
        block_id = block["id"]
        file_name = "image.svg"

        # A new block has no assets:
        self.assertEqual(self._get_library_block_assets(block_id), [])
        self._get_library_block_asset(block_id, file_name, expect_response=404)

        # Upload an asset file
        self._set_library_block_asset(block_id, file_name, SVG_DATA)

        # Get metadata about the uploaded asset file
        metadata = self._get_library_block_asset(block_id, file_name)
        self.assertEqual(metadata["path"], file_name)
        self.assertEqual(metadata["size"], len(SVG_DATA))
        asset_list = self._get_library_block_assets(block_id)
        # We don't just assert that 'asset_list == [metadata]' because that may
        # break in the future if the "get asset" view returns more detail than
        # the "list assets" view.
        self.assertEqual(len(asset_list), 1)
        self.assertEqual(asset_list[0]["path"], metadata["path"])
        self.assertEqual(asset_list[0]["size"], metadata["size"])
        self.assertEqual(asset_list[0]["url"], metadata["url"])

        # Download the file and check that it matches what was uploaded.
        # We need to download using requests since this is served by Blockstore,
        # which the django test client can't interact with.
        content_get_result = requests.get(metadata["url"])
        self.assertEqual(content_get_result.content, SVG_DATA)

        # Set some OLX referencing this asset:
        self._set_library_block_olx(block_id, """
            <html display_name="HTML with Image"><![CDATA[
                <img src="/static/image.svg" alt="An image that says 'SVG is lit' using a fire emoji" />
            ]]></html>
        """)
        # Publish the OLX and the new image file, since published data gets
        # served differently by Blockstore and we should test that too.
        self._commit_library_changes(library["id"])
        metadata = self._get_library_block_asset(block_id, file_name)
        self.assertEqual(metadata["path"], file_name)
        self.assertEqual(metadata["size"], len(SVG_DATA))
        # Download the file from the new URL:
        content_get_result = requests.get(metadata["url"])
        self.assertEqual(content_get_result.content, SVG_DATA)

        # Check that the URL in the student_view gets rewritten:
        fragment = self._render_block_view(block_id, "student_view")
        self.assertNotIn("/static/image.svg", fragment["content"])
        self.assertIn(metadata["url"], fragment["content"])

    def test_asset_filenames(self):
        """
        Test various allowed and disallowed filenames
        """
        library = self._create_library(slug="asset-lib2", title="Static Assets Test Library")
        block = self._add_block_to_library(library["id"], "html", "html1")
        block_id = block["id"]
        file_size = len(SVG_DATA)

        # Unicode names are allowed
        file_name = "🏕.svg"  # (camping).svg
        self._set_library_block_asset(block_id, file_name, SVG_DATA)
        self.assertEqual(self._get_library_block_asset(block_id, file_name)["path"], file_name)
        self.assertEqual(self._get_library_block_asset(block_id, file_name)["size"], file_size)

        # Subfolder names are allowed
        file_name = "transcripts/en.srt"
        self._set_library_block_asset(block_id, file_name, SVG_DATA)
        self.assertEqual(self._get_library_block_asset(block_id, file_name)["path"], file_name)
        self.assertEqual(self._get_library_block_asset(block_id, file_name)["size"], file_size)

        # '../' is definitely not allowed
        file_name = "../definition.xml"
        self._set_library_block_asset(block_id, file_name, SVG_DATA, expect_response=400)

        # 'a////////b' is not allowed
        file_name = "a////////b"
        self._set_library_block_asset(block_id, file_name, SVG_DATA, expect_response=400)
