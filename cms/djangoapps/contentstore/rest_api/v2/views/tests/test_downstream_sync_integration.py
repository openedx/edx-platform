"""
Unit and integration tests to ensure that syncing content from libraries to
courses is working.
"""
from typing import Any
from xml.etree import ElementTree

import ddt
from opaque_keys.edx.locator import LibraryContainerLocator

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import BlockFactory, CourseFactory, ToyCourseFactory
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest


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
                upstream_version="3"
                {self.standard_capa_attributes}
            >multiple choice v2...</problem>
        """)
