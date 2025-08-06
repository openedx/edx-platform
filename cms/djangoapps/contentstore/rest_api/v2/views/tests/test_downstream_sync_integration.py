"""
Unit and integration tests to ensure that syncing content from libraries to
courses is working.
"""
from typing import Any
from xml.etree import ElementTree

import ddt
from opaque_keys.edx.keys import UsageKey

from openedx.core.djangoapps.content_libraries.tests import ContentLibrariesRestApiTest
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import BlockFactory, CourseFactory


@ddt.ddt
class CourseToLibraryTestCase(ContentLibrariesRestApiTest, ModuleStoreTestCase):
    """
    Tests that involve syncing content from libraries to courses.
    """
    maxDiff = None  # Necessary for debugging OLX differences

    def setUp(self):
        super().setUp()
        # self.user is set up by ContentLibrariesRestApiTest

        # The source library (contains the upstreams):
        self.library = self._create_library(slug="testlib", title="Upstream Library")
        lib_id = self.library["id"]  # the library ID as a string
        self.upstream_problem1 = self._add_block_to_library(lib_id, "problem", "prob1", can_stand_alone=True)
        self._set_library_block_olx(
            self.upstream_problem1["id"],
            '<problem display_name="Problem 1 Display Name" weight="1" markdown="MD 1">multiple choice...</problem>'
        )
        self.upstream_problem2 = self._add_block_to_library(lib_id, "problem", "prob2", can_stand_alone=True)
        self._set_library_block_olx(
            self.upstream_problem2["id"],
            '<problem display_name="Problem 2 Display Name" max_attempts="22">multi select...</problem>'
        )
        self.upstream_html1 = self._add_block_to_library(lib_id, "html", "html1", can_stand_alone=False)
        self._set_library_block_olx(
            self.upstream_html1["id"],
            '<html display_name="Text Content">This is the HTML.</html>'
        )
        self.upstream_unit = self._create_container(lib_id, "unit", slug="u1", display_name="Unit 1 Title")
        self._add_container_children(self.upstream_unit["id"], [
            self.upstream_html1["id"],
            self.upstream_problem1["id"],
            self.upstream_problem2["id"],
        ])
        self._commit_library_changes(lib_id)  # publish everything

        # The destination course:
        self.course = CourseFactory.create()
        self.course_section = BlockFactory.create(category='chapter', parent=self.course)
        self.course_subsection = BlockFactory.create(category='sequential', parent=self.course_section)
        self.course_unit = BlockFactory.create(category='vertical', parent=self.course_subsection)

    def _get_sync_status(self, usage_key: str):
        return self._api('get', f"/api/contentstore/v2/downstreams/{usage_key}", {}, expect_response=200)

    def _sync_downstream(self, usage_key: str):
        return self._api('post', f"/api/contentstore/v2/downstreams/{usage_key}/sync", {}, expect_response=200)

    def _get_course_block_olx(self, usage_key: str):
        data = self._api('get', f'/api/olx-export/v1/xblock/{usage_key}/', {}, expect_response=200)
        return data["blocks"][data["root_block_id"]]["olx"]

    def _copy_course_block(self, usage_key: str):
        """
        Copy a course block to the clipboard
        """
        data = self._api(
            'post',
            "/api/content-staging/v1/clipboard/",
            {"usage_key": usage_key},
            expect_response=200
        )
        return data

    def _paste_course_block(self, parent_usage_key: str):
        """
        Paste a course block from the clipboard
        """
        return self._api(
            'post',
            '/xblock/',
            {"parent_locator": parent_usage_key, "staged_content": "clipboard"},
            expect_response=200
        )

    # def _get_course_block_fields(self, usage_key: str):
    #     return self._api('get', f'/xblock/{usage_key}', {}, expect_response=200)

    def _get_course_block_children(self, usage_key: str) -> list[str]:
        """ Get the IDs of the child XBlocks of the given XBlock """
        # TODO: is there really no REST API to get the children of an XBlock in Studio?
        # Maybe this one: /api/contentstore/v1/container/vertical/{usage_key_string}/children
        return [str(k) for k in modulestore().get_item(UsageKey.from_string(usage_key), depth=0).children]

    def _create_block_from_upstream(
        self,
        block_category: str,
        parent_usage_key: str,
        upstream_key: str,
        expect_response: int = 200,
    ):
        """
        Call the CMS API for inserting an XBlock that's cloned from a library
        item. i.e. copy a *published* library block into a course, and create an
        upstream link.
        """
        return self._api('post', "/xblock/", {
            "category": block_category,
            "parent_locator": parent_usage_key,
            "library_content_key": upstream_key,
        }, expect_response=expect_response)

    def _update_course_block_fields(self, usage_key: str, fields: dict[str, Any] = None):
        """ Update fields of an XBlock """
        return self._api('patch', f"/xblock/{usage_key}", {
            "metadata": fields,
        }, expect_response=200)

    def assertXmlEqual(self, xml_str_a: str, xml_str_b: str) -> bool:
        """ Assert that the given XML strings are equal, ignoring attribute order and some whitespace variations. """
        self.assertEqual(
            ElementTree.canonicalize(xml_str_a, strip_text=True),
            ElementTree.canonicalize(xml_str_b, strip_text=True),
        )

    # OLX attributes that will appear on capa problems when saved/exported. Excludes "markdown"
    standard_capa_attributes = """
        markdown_edited="false"
        matlab_api_key="null"
        name="null"
        rerandomize="never"
        source_code="null"
        tags="[]"
        use_latex_compiler="false"
    """

    ####################################################################################################################

    def test_problem_sync(self):
        """
        Test that we can sync a problem from a library into a course.
        """
        # 1️⃣ First, create the problem in the course, using the upstream problem as a template:
        downstream_problem1 = self._create_block_from_upstream(
            block_category="problem",
            parent_usage_key=str(self.course_subsection.usage_key),
            upstream_key=self.upstream_problem1["id"],
        )
        status = self._get_sync_status(downstream_problem1["locator"])
        self.assertDictContainsEntries(status, {
            'upstream_ref': self.upstream_problem1["id"],  # e.g. 'lb:CL-TEST:testlib:problem:prob1'
            'version_available': 2,
            'version_synced': 2,
            'version_declined': None,
            'ready_to_sync': False,
            'error_message': None,
            'is_modified': False,
            # 'upstream_link': 'http://course-authoring-mfe/library/lib:CL-TEST:testlib/components?usageKey=...'
        })
        assert status["upstream_link"].startswith("http://course-authoring-mfe/library/")
        assert status["upstream_link"].endswith(f"/components?usageKey={self.upstream_problem1['id']}")

        # Check the OLX of the downstream block. Notice that:
        # (1) fields display_name and markdown, as well as the 'data' (content/body of the <problem>) are synced.
        # (2) per UpstreamSyncMixin.get_customizable_fields(), some fields like weight and max_attempts are
        #     DROPPED entirely from the upstream version when creating the downstream:
        self.assertXmlEqual(self._get_course_block_olx(downstream_problem1["locator"]), f"""
            <problem
                display_name="Problem 1 Display Name"
                markdown="MD 1"
                upstream="{self.upstream_problem1['id']}"
                upstream_display_name="Problem 1 Display Name"
                upstream_version="2"
                {self.standard_capa_attributes}
            >multiple choice...</problem>
        """)

        # 2️⃣ Now, lets modify the upstream problem AND the downstream problem:

        self._update_course_block_fields(downstream_problem1["locator"], {
            "display_name": "Custom Display Name",
            "max_attempts": 3,
            "markdown": "blow me away, scotty!",  # This change will be lost
        })

        self._set_library_block_olx(
            self.upstream_problem1["id"],
            '<problem display_name="Problem 1 NEW name" markdown="updated">multiple choice v2...</problem>'
        )
        self._publish_library_block(self.upstream_problem1["id"])

        # Here's how the downstream OLX looks now, before we sync:
        self.assertXmlEqual(self._get_course_block_olx(downstream_problem1["locator"]), f"""
            <problem
                display_name="Custom Display Name"
                markdown="blow me away, scotty!"
                max_attempts="3"
                upstream="{self.upstream_problem1['id']}"
                upstream_display_name="Problem 1 Display Name"
                upstream_version="2"
                downstream_customized="[&quot;display_name&quot;]"
                {self.standard_capa_attributes}
            >multiple choice...</problem>
        """)

        status = self._get_sync_status(downstream_problem1["locator"])
        self.assertDictContainsEntries(status, {
            'upstream_ref': self.upstream_problem1["id"],  # e.g. 'lb:CL-TEST:testlib:problem:prob1'
            'version_available': 3,  # <--- updated
            'version_synced': 2,
            'version_declined': None,
            'ready_to_sync': True,  # <--- updated
            'error_message': None,
            'is_modified': True,
        })

        # 3️⃣ Now, sync and check the resulting OLX of the downstream

        self._sync_downstream(downstream_problem1["locator"])

        # Here's how the downstream OLX looks now, after we synced it.
        # Notice:
        #   (1) content like "markdown" and the body XML content are synced
        #   (2) the "display_name" is left alone (customized downstream), but
        #   (3) "upstream_display_name" is updated.
        #   (4) The customized "max_attempts" is also still present.
        self.assertXmlEqual(self._get_course_block_olx(downstream_problem1["locator"]), f"""
            <problem
                display_name="Custom Display Name"
                markdown="updated"
                max_attempts="3"
                upstream="{self.upstream_problem1['id']}"
                upstream_display_name="Problem 1 NEW name"
                downstream_customized="[&quot;display_name&quot;]"
                upstream_version="3"
                {self.standard_capa_attributes}
            >multiple choice v2...</problem>
        """)

    def test_unit_sync(self):
        """
        Test that we can sync a unit from the library into the course
        """
        # 1️⃣ Create a "vertical" block in the course based on a "unit" container:
        downstream_unit = self._create_block_from_upstream(
            # The API consumer needs to specify "vertical" here, even though upstream is "unit".
            # In the future we could create a nicer REST API endpoint for this that's not part of
            # the messy '/xblock/' API and which auto-detects the types based on the upstream_key.
            block_category="vertical",
            parent_usage_key=str(self.course_subsection.usage_key),
            upstream_key=self.upstream_unit["id"],
        )
        status = self._get_sync_status(downstream_unit["locator"])
        self.assertDictContainsEntries(status, {
            'upstream_ref': self.upstream_unit["id"],  # e.g. 'lct:CL-TEST:testlib:unit:u1'
            'version_available': 2,
            'version_synced': 2,
            'version_declined': None,
            'ready_to_sync': False,
            'error_message': None,
            'is_modified': False,
            # 'upstream_link': 'http://course-authoring-mfe/library/lib:CL-TEST:testlib/units/...'
        })
        assert status["upstream_link"].startswith("http://course-authoring-mfe/library/")
        assert status["upstream_link"].endswith(f"/units/{self.upstream_unit['id']}")

        # Check that the downstream container matches our expectations.
        # Note that:
        # (1) Every XBlock has an "upstream" field
        # (2) some "downstream only" fields like weight and max_attempts are omitted.
        self.assertXmlEqual(self._get_course_block_olx(downstream_unit["locator"]), f"""
            <vertical
                display_name="Unit 1 Title"
                upstream_display_name="Unit 1 Title"
                upstream="{self.upstream_unit['id']}"
                upstream_version="2"
            >
                <html
                    display_name="Text Content"
                    upstream_display_name="Text Content"
                    editor="visual"
                    upstream="{self.upstream_html1['id']}"
                    upstream_version="2"
                    upstream_data="This is the HTML."
                >This is the HTML.</html>
                <problem
                    display_name="Problem 1 Display Name"
                    upstream_display_name="Problem 1 Display Name"
                    markdown="MD 1"
                    {self.standard_capa_attributes}
                    upstream="{self.upstream_problem1['id']}"
                    upstream_version="2"
                >multiple choice...</problem>
                <problem
                    display_name="Problem 2 Display Name"
                    upstream_display_name="Problem 2 Display Name"
                    markdown="null"
                    {self.standard_capa_attributes}
                    upstream="{self.upstream_problem2['id']}"
                    upstream_version="2"
                >multi select...</problem>
            </vertical>
        """)

    # 2️⃣ Now, lets modify the upstream problem 1:

        self._set_library_block_olx(
            self.upstream_problem1["id"],
            '<problem display_name="Problem 1 NEW name" markdown="updated">multiple choice v2...</problem>'
        )
        self._publish_container(self.upstream_unit["id"])

        status = self._get_sync_status(downstream_unit["locator"])
        self.assertDictContainsEntries(status, {
            'upstream_ref': self.upstream_unit["id"],  # e.g. 'lct:CL-TEST:testlib:unit:u1'
            'version_available': 2,  # <--- not updated since we didn't directly modify the unit
            'version_synced': 2,
            'version_declined': None,
            # FIXME: ready_to_sync should be true, since a child block needs syncing.
            # This may need to be fixed post-Teak, as syncing the children directly is still possible.
            'ready_to_sync': False,
            'error_message': None,
            'is_modified': False,
        })

        # Check the upstream/downstream status of [one of] the children

        downstream_problem1 = self._get_course_block_children(downstream_unit["locator"])[1]
        assert "type@problem" in downstream_problem1
        self.assertDictContainsEntries(self._get_sync_status(downstream_problem1), {
            'upstream_ref': self.upstream_problem1["id"],
            'version_available': 3,  # <--- updated since we modified the problem
            'version_synced': 2,
            'version_declined': None,
            'ready_to_sync': True,  # <--- updated
            'error_message': None,
            'is_modified': False,
        })

        # 3️⃣ Now, sync and check the resulting OLX of the downstream

        self._sync_downstream(downstream_unit["locator"])

        self.assertXmlEqual(self._get_course_block_olx(downstream_unit["locator"]), f"""
            <vertical
                display_name="Unit 1 Title"
                upstream_display_name="Unit 1 Title"
                upstream="{self.upstream_unit['id']}"
                upstream_version="2"
            >
                <html
                    display_name="Text Content"
                    upstream_display_name="Text Content"
                    editor="visual"
                    upstream="{self.upstream_html1['id']}"
                    upstream_version="2"
                    upstream_data="This is the HTML."
                >This is the HTML.</html>
                <!-- 🟢 the problem below has been updated: -->
                <problem
                    display_name="Problem 1 NEW name"
                    upstream_display_name="Problem 1 NEW name"
                    markdown="updated"
                    {self.standard_capa_attributes}
                    upstream="{self.upstream_problem1['id']}"
                    upstream_version="3"
                >multiple choice v2...</problem>
                <problem
                    display_name="Problem 2 Display Name"
                    upstream_display_name="Problem 2 Display Name"
                    markdown="null"
                    {self.standard_capa_attributes}
                    upstream="{self.upstream_problem2['id']}"
                    upstream_version="2"
                >multi select...</problem>
            </vertical>
        """)

        #   Now, add and delete a component
        upstream_problem3 = self._add_block_to_library(
            self.library["id"],
            "problem",
            "prob3",
            can_stand_alone=True
        )
        self._set_library_block_olx(
            upstream_problem3["id"],
            '<problem display_name="Problem 3 Display Name" max_attempts="22">single select...</problem>'
        )
        self._add_container_children(self.upstream_unit["id"], [upstream_problem3["id"]])
        self._remove_container_components(self.upstream_unit["id"], [self.upstream_problem2["id"]])
        self._commit_library_changes(self.library["id"])  # publish everything

        status = self._get_sync_status(downstream_unit["locator"])
        self.assertDictContainsEntries(status, {
            'upstream_ref': self.upstream_unit["id"],  # e.g. 'lct:CL-TEST:testlib:unit:u1'
            'version_available': 4,  # <--- updated twice, delete and add component
            'version_synced': 2,
            'version_declined': None,
            'ready_to_sync': True,
            'error_message': None,
            'is_modified': False,
        })

        # 3️⃣ Now, sync and check the resulting OLX of the downstream

        self._sync_downstream(downstream_unit["locator"])
        self.assertXmlEqual(self._get_course_block_olx(downstream_unit["locator"]), f"""
            <vertical
                display_name="Unit 1 Title"
                upstream_display_name="Unit 1 Title"
                upstream="{self.upstream_unit['id']}"
                upstream_version="4"
            >
                <html
                    display_name="Text Content"
                    upstream_display_name="Text Content"
                    editor="visual"
                    upstream="{self.upstream_html1['id']}"
                    upstream_version="2"
                    upstream_data="This is the HTML."
                >This is the HTML.</html>
                <problem
                    display_name="Problem 1 NEW name"
                    upstream_display_name="Problem 1 NEW name"
                    markdown="updated"
                    {self.standard_capa_attributes}
                    upstream="{self.upstream_problem1['id']}"
                    upstream_version="3"
                >multiple choice v2...</problem>
                <!-- 🟢 the problem 2 has been deleted: -->
                <!-- 🟢 the problem 3 has been added: -->
                <problem
                    display_name="Problem 3 Display Name"
                    upstream_display_name="Problem 3 Display Name"
                    markdown="null"
                    {self.standard_capa_attributes}
                    upstream="{upstream_problem3['id']}"
                    upstream_version="2"
                >single select...</problem>
            </vertical>
        """)

        #   Now, reorder components
        self._patch_container_components(self.upstream_unit["id"], [
            upstream_problem3["id"],
            self.upstream_problem1["id"],
            self.upstream_html1["id"],
        ])
        self._publish_container(self.upstream_unit["id"])

        # 3️⃣ Now, sync and check the resulting OLX of the downstream

        self._sync_downstream(downstream_unit["locator"])
        self.assertXmlEqual(self._get_course_block_olx(downstream_unit["locator"]), f"""
            <vertical
                display_name="Unit 1 Title"
                upstream_display_name="Unit 1 Title"
                upstream="{self.upstream_unit['id']}"
                upstream_version="5"
            >
                <!-- 🟢 the problem 3 has been moved to top: -->
                <problem
                    display_name="Problem 3 Display Name"
                    upstream_display_name="Problem 3 Display Name"
                    markdown="null"
                    {self.standard_capa_attributes}
                    upstream="{upstream_problem3['id']}"
                    upstream_version="2"
                >single select...</problem>
                <!-- 🟢 the problem 1 has been moved to middle: -->
                <problem
                    display_name="Problem 1 NEW name"
                    upstream_display_name="Problem 1 NEW name"
                    markdown="updated"
                    {self.standard_capa_attributes}
                    upstream="{self.upstream_problem1['id']}"
                    upstream_version="3"
                >multiple choice v2...</problem>
                <!-- 🟢 the html 1 has been moved to end: -->
                <html
                    display_name="Text Content"
                    upstream_display_name="Text Content"
                    editor="visual"
                    upstream="{self.upstream_html1['id']}"
                    upstream_version="2"
                    upstream_data="This is the HTML."
                >This is the HTML.</html>
            </vertical>
        """)

    def test_html_sync_and_copy_paste(self):
        """
        Test that we can sync a html from a library into a course.
        """
        # 1️⃣ First, create the html in the course, using the upstream problem as a template:
        downstream_html1 = self._create_block_from_upstream(
            block_category="html",
            parent_usage_key=str(self.course_subsection.usage_key),
            upstream_key=self.upstream_html1["id"],
        )
        status = self._get_sync_status(downstream_html1["locator"])
        self.assertDictContainsEntries(status, {
            'upstream_ref': self.upstream_html1["id"],  # e.g. 'lb:CL-TEST:testlib:html:html1'
            'version_available': 2,
            'version_synced': 2,
            'version_declined': None,
            'ready_to_sync': False,
            'error_message': None,
            'is_modified': False,
            # 'upstream_link': 'http://course-authoring-mfe/library/lib:CL-TEST:testlib/components?usageKey=...'
        })
        assert status["upstream_link"].startswith("http://course-authoring-mfe/library/")
        assert status["upstream_link"].endswith(f"/components?usageKey={self.upstream_html1['id']}")

        # Check the OLX of the downstream block. Notice that:
        # (1) fields display_name and data (content/body of the <html>) are synced.
        self.assertXmlEqual(self._get_course_block_olx(downstream_html1["locator"]), f"""
            <html
                display_name="Text Content"
                editor="visual"
                upstream="{self.upstream_html1['id']}"
                upstream_display_name="Text Content"
                upstream_version="2"
                upstream_data="This is the HTML."
            >This is the HTML.</html>
        """)

        # 2️⃣ Now, lets modify the upstream html AND the downstream html:

        self._update_course_block_fields(downstream_html1["locator"], {
            "display_name": "Text Content",
            "data": "The new downstream data.",  # This change will be stay
        })

        self._set_library_block_olx(
            self.upstream_html1["id"],
            '<html display_name="HTML 1 NEW name">The new upstream data.</html>'
        )
        self._publish_library_block(self.upstream_html1["id"])

        # Here's how the downstream OLX looks now, before we sync:
        self.assertXmlEqual(self._get_course_block_olx(downstream_html1["locator"]), f"""
            <html
                display_name="Text Content"
                downstream_customized="[&quot;data&quot;]"
                editor="visual"
                upstream="{self.upstream_html1['id']}"
                upstream_display_name="Text Content"
                upstream_version="2"
                upstream_data="This is the HTML."
            >The new downstream data.</html>
        """)

        status = self._get_sync_status(downstream_html1["locator"])
        self.assertDictContainsEntries(status, {
            'upstream_ref': self.upstream_html1["id"],  # e.g. 'lb:CL-TEST:testlib:html:html1'
            'version_available': 3,  # <--- updated
            'version_synced': 2,
            'version_declined': None,
            'ready_to_sync': True,  # <--- updated
            'error_message': None,
            'is_modified': True,
        })

        # 3️⃣ Now, sync and check the resulting OLX of the downstream

        self._sync_downstream(downstream_html1["locator"])

        # Here's how the downstream OLX looks now, after we synced it.
        # Notice:
        #   (1) "display_name" field is synced as it was not customized in course.
        #   (2) the "data" is left alone (customized downstream), but
        #   (3) "upstream_data" is updated.
        self.assertXmlEqual(self._get_course_block_olx(downstream_html1["locator"]), f"""
            <html
                display_name="HTML 1 NEW name"
                editor="visual"
                upstream="{self.upstream_html1['id']}"
                upstream_display_name="HTML 1 NEW name"
                upstream_version="3"
                upstream_data="The new upstream data."
                downstream_customized="[&quot;data&quot;]"
            >The new downstream data.</html>
        """)

        # Copy this modified html block
        self._copy_course_block(downstream_html1["locator"])
        # Paste it
        pasted_block = self._paste_course_block(str(self.course_subsection.usage_key))

        # The pasted block will have same fields as the above block except the
        # upstream_* fields will now have the original blocks base value, so
        # pasted_block.upstream_display_name == downstream_html1.display_name
        # pasted_block.upstream_data == downstream_html1.data
        # while still have `downstream_customized` same to avoid overriding during sync
        # to allow authors to revert back to back to the original copied customized value

        # See `upstream_data` below is same as how downstream_html1.data is set.
        self.assertXmlEqual(self._get_course_block_olx(pasted_block["locator"]), f"""
            <html
                display_name="HTML 1 NEW name"
                editor="visual"
                upstream="{self.upstream_html1['id']}"
                upstream_display_name="HTML 1 NEW name"
                upstream_version="3"
                upstream_data="The new downstream data."
                downstream_customized="[&quot;data&quot;]"
            >The new downstream data.</html>
        """)
