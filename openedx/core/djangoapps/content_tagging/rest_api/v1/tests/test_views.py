"""
Tests tagging rest api views
"""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import abc
import ddt
from django.contrib.auth import get_user_model
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from openedx_tagging.core.tagging.models import Tag, Taxonomy
from openedx_tagging.core.tagging.models.system_defined import SystemDefinedTaxonomy
from openedx_tagging.core.tagging.rest_api.v1.serializers import TaxonomySerializer
from organizations.models import Organization
from rest_framework import status
from rest_framework.test import APITestCase

from common.djangoapps.student.auth import add_users, update_org_role
from common.djangoapps.student.roles import (
    CourseInstructorRole,
    CourseStaffRole,
    OrgContentCreatorRole,
    OrgInstructorRole,
    OrgLibraryUserRole,
    OrgStaffRole,
)
from openedx.core.djangoapps.content_libraries.api import (
    AccessLevel,
    create_library,
    COMPLEX,
    set_library_user_permissions,
)
from openedx.core.djangoapps.content_tagging.models import TaxonomyOrg
from openedx.core.djangolib.testing.utils import skip_unless_cms
from openedx.core.lib import blockstore_api

User = get_user_model()

TAXONOMY_ORG_LIST_URL = "/api/content_tagging/v1/taxonomies/"
TAXONOMY_ORG_DETAIL_URL = "/api/content_tagging/v1/taxonomies/{pk}/"
OBJECT_TAG_UPDATE_URL = "/api/content_tagging/v1/object_tags/{object_id}/?taxonomy={taxonomy_id}"
TAXONOMY_TEMPLATE_URL = "/api/content_tagging/v1/taxonomies/import/{filename}"


def check_taxonomy(
    data,
    pk,
    name,
    description=None,
    enabled=True,
    allow_multiple=True,
    allow_free_text=False,
    system_defined=False,
    visible_to_authors=True,
    **_
):
    """
    Check the given data against the expected values.
    """
    assert data["id"] == pk
    assert data["name"] == name
    assert data["description"] == description
    assert data["enabled"] == enabled
    assert data["allow_multiple"] == allow_multiple
    assert data["allow_free_text"] == allow_free_text
    assert data["system_defined"] == system_defined
    assert data["visible_to_authors"] == visible_to_authors


class TestTaxonomyObjectsMixin:
    """
    Sets up data for testing Content Taxonomies.
    """
    def _setUp_orgs(self):
        """
        Create orgs for testing
        """
        self.orgA = Organization.objects.create(name="Organization A", short_name="orgA")
        self.orgB = Organization.objects.create(name="Organization B", short_name="orgB")
        self.orgX = Organization.objects.create(name="Organization X", short_name="orgX")

    def _setUp_courses(self):
        """
        Create courses for testing
        """
        self.courseA = CourseLocator("orgA", "101", "test")
        self.courseB = CourseLocator("orgB", "101", "test")

    def _setUp_library(self):
        """
        Create library for testing
        """
        self.collection = blockstore_api.create_collection("Test library collection")
        self.content_libraryA = create_library(
            collection_uuid=self.collection.uuid,
            org=self.orgA,
            slug="lib_a",
            library_type=COMPLEX,
            title="Library Org A",
            description="This is a library from Org A",
            allow_public_learning=False,
            allow_public_read=False,
            library_license="",
        )

    def _setUp_users(self):
        """
        Create users for testing
        """
        self.user = User.objects.create(
            username="user",
            email="user@example.com",
        )
        self.staff = User.objects.create(
            username="staff",
            email="staff@example.com",
            is_staff=True,
        )

        self.staffA = User.objects.create(
            username="staffA",
            email="userA@example.com",
        )
        update_org_role(self.staff, OrgStaffRole, self.staffA, [self.orgA.short_name])

        self.content_creatorA = User.objects.create(
            username="content_creatorA",
            email="content_creatorA@example.com",
        )
        update_org_role(self.staff, OrgContentCreatorRole, self.content_creatorA, [self.orgA.short_name])

        self.instructorA = User.objects.create(
            username="instructorA",
            email="instructorA@example.com",
        )
        update_org_role(self.staff, OrgInstructorRole, self.instructorA, [self.orgA.short_name])

        self.library_staffA = User.objects.create(
            username="library_staffA",
            email="library_staffA@example.com",
        )
        update_org_role(self.staff, OrgLibraryUserRole, self.library_staffA, [self.orgA.short_name])

        self.course_instructorA = User.objects.create(
            username="course_instructorA",
            email="course_instructorA@example.com",
        )
        add_users(self.staff, CourseInstructorRole(self.courseA), self.course_instructorA)

        self.course_staffA = User.objects.create(
            username="course_staffA",
            email="course_staffA@example.com",
        )
        add_users(self.staff, CourseStaffRole(self.courseA), self.course_staffA)

        self.library_userA = User.objects.create(
            username="library_userA",
            email="library_userA@example.com",
        )
        set_library_user_permissions(
            self.content_libraryA.key,
            self.library_userA,
            AccessLevel.READ_LEVEL
        )

    def _setUp_taxonomies(self):
        """
        Create taxonomies for testing
        """
        # Orphaned taxonomy
        self.ot1 = Taxonomy.objects.create(name="ot1", enabled=True)
        self.ot2 = Taxonomy.objects.create(name="ot2", enabled=False)

        # System defined taxonomy
        self.st1 = Taxonomy.objects.create(name="st1", enabled=True)
        self.st1.taxonomy_class = SystemDefinedTaxonomy
        self.st1.save()
        TaxonomyOrg.objects.create(
            taxonomy=self.st1,
            rel_type=TaxonomyOrg.RelType.OWNER,
            org=None,
        )
        self.st2 = Taxonomy.objects.create(name="st2", enabled=False)
        self.st2.taxonomy_class = SystemDefinedTaxonomy
        self.st2.save()
        TaxonomyOrg.objects.create(
            taxonomy=self.st2,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )

        # Global taxonomy
        self.t1 = Taxonomy.objects.create(name="t1", enabled=True)
        TaxonomyOrg.objects.create(
            taxonomy=self.t1,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )
        self.t2 = Taxonomy.objects.create(name="t2", enabled=False)
        TaxonomyOrg.objects.create(
            taxonomy=self.t2,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )

        # OrgA taxonomy
        self.tA1 = Taxonomy.objects.create(name="tA1", enabled=True)
        TaxonomyOrg.objects.create(
            taxonomy=self.tA1,
            org=self.orgA, rel_type=TaxonomyOrg.RelType.OWNER,)
        self.tA2 = Taxonomy.objects.create(name="tA2", enabled=False)
        TaxonomyOrg.objects.create(
            taxonomy=self.tA2,
            org=self.orgA,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )

        # OrgB taxonomy
        self.tB1 = Taxonomy.objects.create(name="tB1", enabled=True)
        TaxonomyOrg.objects.create(
            taxonomy=self.tB1,
            org=self.orgB,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )
        self.tB2 = Taxonomy.objects.create(name="tB2", enabled=False)
        TaxonomyOrg.objects.create(
            taxonomy=self.tB2,
            org=self.orgB,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )

        # OrgA and OrgB taxonomy
        self.tBA1 = Taxonomy.objects.create(name="tBA1", enabled=True)
        TaxonomyOrg.objects.create(
            taxonomy=self.tBA1,
            org=self.orgA,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )
        TaxonomyOrg.objects.create(
            taxonomy=self.tBA1,
            org=self.orgB,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )
        self.tBA2 = Taxonomy.objects.create(name="tBA2", enabled=False)
        TaxonomyOrg.objects.create(
            taxonomy=self.tBA2,
            org=self.orgA,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )
        TaxonomyOrg.objects.create(
            taxonomy=self.tBA2,
            org=self.orgB,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )

    def setUp(self):

        super().setUp()

        self._setUp_orgs()
        self._setUp_courses()
        self._setUp_library()
        self._setUp_users()
        self._setUp_taxonomies()


@skip_unless_cms
@ddt.ddt
class TestTaxonomyListCreateViewSet(TestTaxonomyObjectsMixin, APITestCase):
    """
    Test cases for TaxonomyViewSet for list and create actions
    """

    def _test_list_taxonomy(
            self,
            user_attr: str,
            expected_taxonomies: list[str],
            enabled_parameter: bool | None = None,
            org_parameter: str | None = None
    ) -> None:
        """
        Helper function to call the list endpoint and check the response
        """
        url = TAXONOMY_ORG_LIST_URL

        user = getattr(self, user_attr)
        self.client.force_authenticate(user=user)

        # Set parameters cleaning empty values
        query_params = {k: v for k, v in {"enabled": enabled_parameter, "org": org_parameter}.items() if v is not None}

        response = self.client.get(url, query_params, format="json")

        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(set(t["name"] for t in response.data["results"]), set(expected_taxonomies))

    def test_list_taxonomy_staff(self) -> None:
        """
        Tests that staff users see all taxonomies
        """
        # Default page_size=10, and so "tBA1" and "tBA2" appear on the second page
        expected_taxonomies = ["ot1", "ot2", "st1", "st2", "t1", "t2", "tA1", "tA2", "tB1", "tB2"]
        self._test_list_taxonomy(
            user_attr="staff",
            expected_taxonomies=expected_taxonomies,
        )

    @ddt.data(
        "content_creatorA",
        "instructorA",
        "library_staffA",
        "course_instructorA",
        "course_staffA",
        "library_userA",
    )
    def test_list_taxonomy_orgA(self, user_attr: str) -> None:
        """
        Tests that non staff users from orgA can see only enabled taxonomies from orgA and global taxonomies
        """
        expected_taxonomies = ["st1", "t1", "tA1", "tBA1"]
        self._test_list_taxonomy(
            user_attr=user_attr,
            enabled_parameter=True,
            expected_taxonomies=expected_taxonomies,
        )

    @ddt.data(
        (True, ["ot1", "st1", "t1", "tA1", "tB1", "tBA1"]),
        (False, ["ot2", "st2", "t2", "tA2", "tB2", "tBA2"]),
    )
    @ddt.unpack
    def test_list_taxonomy_enabled_filter(self, enabled_parameter: bool, expected_taxonomies: list[str]) -> None:
        """
        Tests that the enabled filter works as expected
        """
        self._test_list_taxonomy(
            user_attr="staff",
            enabled_parameter=enabled_parameter,
            expected_taxonomies=expected_taxonomies
        )

    @ddt.data(
        ("orgA", ["st1", "st2", "t1", "t2", "tA1", "tA2", "tBA1", "tBA2"]),
        ("orgB", ["st1", "st2", "t1", "t2", "tB1", "tB2", "tBA1", "tBA2"]),
        ("orgX", ["st1", "st2", "t1", "t2"]),
    )
    @ddt.unpack
    def test_list_taxonomy_org_filter(self, org_parameter: str, expected_taxonomies: list[str]) -> None:
        """
        Tests that the org filter works as expected
        """
        self._test_list_taxonomy(
            user_attr="staff",
            org_parameter=org_parameter,
            expected_taxonomies=expected_taxonomies,
        )

    def test_list_taxonomy_invalid_org(self) -> None:
        """
        Tests that using an invalid org in the filter will raise BAD_REQUEST
        """
        url = TAXONOMY_ORG_LIST_URL

        self.client.force_authenticate(user=self.staff)

        query_params = {"org": "invalidOrg"}

        response = self.client.get(url, query_params, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @ddt.data(
        ("user", (), None),
        ("staffA", ["tA2", "tBA1", "tBA2"], None),
        ("staff", ["st2", "t1", "t2"], "3"),
    )
    @ddt.unpack
    def test_list_taxonomy_pagination(
        self, user_attr: str, expected_taxonomies: list[str], expected_next_page: str | None
    ) -> None:
        """
        Tests that the pagination works as expected
        """
        url = TAXONOMY_ORG_LIST_URL

        user = getattr(self, user_attr)
        self.client.force_authenticate(user=user)

        query_params = {"page_size": 3, "page": 2}

        response = self.client.get(url, query_params, format="json")

        assert response.status_code == status.HTTP_200_OK if len(expected_taxonomies) > 0 else status.HTTP_404_NOT_FOUND
        if status.is_success(response.status_code):
            self.assertEqual(set(t["name"] for t in response.data["results"]), set(expected_taxonomies))
            parsed_url = urlparse(response.data["next"])

            next_page = parse_qs(parsed_url.query).get("page", [None])[0]
            assert next_page == expected_next_page

    def test_list_invalid_page(self) -> None:
        """
        Tests that using an invalid page will raise NOT_FOUND
        """
        url = TAXONOMY_ORG_LIST_URL

        self.client.force_authenticate(user=self.user)

        query_params = {"page": 123123}

        response = self.client.get(url, query_params, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @ddt.data(
        (None, status.HTTP_401_UNAUTHORIZED),
        ("user", status.HTTP_403_FORBIDDEN),
        ("content_creatorA", status.HTTP_403_FORBIDDEN),
        ("instructorA", status.HTTP_403_FORBIDDEN),
        ("library_staffA", status.HTTP_403_FORBIDDEN),
        ("course_instructorA", status.HTTP_403_FORBIDDEN),
        ("course_staffA", status.HTTP_403_FORBIDDEN),
        ("library_userA", status.HTTP_403_FORBIDDEN),
        ("staffA", status.HTTP_201_CREATED),
        ("staff", status.HTTP_201_CREATED),
    )
    @ddt.unpack
    def test_create_taxonomy(self, user_attr: str, expected_status: int) -> None:
        """
        Tests that only Taxonomy admins and org level admins can create taxonomies
        """
        url = TAXONOMY_ORG_LIST_URL

        create_data = {
            "name": "taxonomy_data",
            "description": "This is a description",
            "enabled": True,
            "allow_multiple": True,
        }

        if user_attr:
            user = getattr(self, user_attr)
            self.client.force_authenticate(user=user)

        response = self.client.post(url, create_data, format="json")
        assert response.status_code == expected_status

        # If we were able to create the taxonomy, check if it was created
        if status.is_success(expected_status):
            check_taxonomy(response.data, response.data["id"], **create_data)
            url = TAXONOMY_ORG_DETAIL_URL.format(pk=response.data["id"])

            response = self.client.get(url)
            check_taxonomy(response.data, response.data["id"], **create_data)

            # Also checks if the taxonomy was associated with the org
            if user_attr == "staffA":
                assert TaxonomyOrg.objects.filter(taxonomy=response.data["id"], org=self.orgA).exists()


@ddt.ddt
class TestTaxonomyDetailExportMixin(TestTaxonomyObjectsMixin):
    """
    Test cases to be used with detail and export actions
    """

    @abc.abstractmethod
    def _test_api_call(self, **_kwargs) -> None:
        """
        Helper function to call the detail/export endpoint and check the response
        """

    @ddt.data(
        "user",
        "content_creatorA",
        "instructorA",
        "library_staffA",
        "course_instructorA",
        "course_staffA",
        "library_userA",
    )
    def test_detail_taxonomy_all_org_enabled(self, user_attr: str) -> None:
        """
        Tests that everyone can see enabled global taxonomies
        """
        self._test_api_call(
            user_attr=user_attr,
            taxonomy_attr="t1",
            expected_status=status.HTTP_200_OK,
            reason="Everyone should see enabled global taxonomies",
        )

    @ddt.data(
        ("content_creatorA", "tA1", "User with OrgContentCreatorRole(orgA) should see an enabled taxonomy from orgA"),
        ("content_creatorA", "tBA1", "User with OrgContentCreatorRole(orgA) should see an enabled taxonomy from orgA"),
        ("content_creatorA", "t1", "User with OrgContentCreatorRole(orgA) should see an enabled global taxonomy"),
        ("instructorA", "tA1", "User with OrgInstructorRole(orgA) should see an enabled taxonomy from orgA"),
        ("instructorA", "tBA1", "User with OrgInstructorRole(orgA) should see an enabled taxonomy from orgA"),
        ("instructorA", "t1", "User with OrgInstructorRole(orgA) should see an enabled global taxonomy"),
        ("library_staffA", "tA1", "User with OrgLibraryUserRole(orgA) should see an enabled taxonomy from orgA"),
        ("library_staffA", "tBA1", "User with OrgLibraryUserRole(orgA) should see an enabled taxonomy from orgA"),
        ("library_staffA", "t1", "User with OrgInstructorRole(orgA) should see an enabled global taxonomy"),
        (
            "course_instructorA",
            "tA1",
            "User with CourseInstructorRole in a course from orgA should see an enabled taxonomy from orgA"
        ),
        (
            "course_instructorA",
            "tBA1",
            "User with CourseInstructorRole in a course from orgA should see an enabled taxonomy from orgA"
        ),
        (
            "course_instructorA",
            "t1",
            "User with CourseInstructorRole in a course from orgA should see an enabled global taxonomy"
        ),
        (
            "course_staffA",
            "tA1",
            "User with CourseStaffRole in a course from orgA should see an enabled taxonomy from orgA"
        ),
        (
            "course_staffA",
            "tBA1",
            "User with CourseStaffRole in a course from orgA should see an enabled taxonomy from orgA"
        ),
        (
            "course_staffA",
            "t1",
            "User with CourseStaffRole in a course from orgA should see an enabled global taxonomy"
        ),
        (
            "library_userA",
            "tA1",
            "User with permission on a library from orgA should see an enabled taxonomy from orgA"
        ),
        (
            "library_userA",
            "tBA1",
            "User with permission on a library from orgA should see an enabled taxonomy from orgA"
        ),
        (
            "library_userA",
            "t1",
            "User with permission on a library from orgA should see an enabled global taxonomy"
        ),
    )
    @ddt.unpack
    def test_detail_taxonomy_org_user_see_enabled(self, user_attr: str, taxonomy_attr: str, reason: str) -> None:
        """
        Tests that org users (content creators and instructors) can see enabled global taxonomies and taxonomies
        from their orgs
        """
        self._test_api_call(
            user_attr=user_attr,
            taxonomy_attr=taxonomy_attr,
            expected_status=status.HTTP_200_OK,
            reason=reason,
        )

    @ddt.data(
        "tA2",
        "tBA2",
    )
    def test_detail_taxonomy_org_admin_see_disabled(self, taxonomy_attr: str) -> None:
        """
        Tests that org admins can see disabled taxonomies from their orgs
        """
        self._test_api_call(
            user_attr="staffA",
            taxonomy_attr=taxonomy_attr,
            expected_status=status.HTTP_200_OK,
            reason="User with OrgContentCreatorRole(orgA) should see a disabled taxonomy from orgA",
        )

    @ddt.data(
        "st2",
        "t2",
    )
    def test_detail_taxonomy_org_admin_dont_see_disabled_global(self, taxonomy_attr: str) -> None:
        """
        Tests that org admins can't see disabled global taxonomies
        """
        self._test_api_call(
            user_attr="staffA",
            taxonomy_attr=taxonomy_attr,
            expected_status=status.HTTP_404_NOT_FOUND,
            reason="User with OrgContentCreatorRole(orgA) shouldn't see a disabled global taxonomy",
        )

    @ddt.data(
        ("content_creatorA", "t2", "User with OrgContentCreatorRole(orgA) shouldn't see a disabled global taxonomy"),
        ("instructorA", "tA2", "User with OrgInstructorRole(orgA) shouldn't see a disabled taxonomy from orgA"),
        ("instructorA", "tBA2", "User with OrgInstructorRole(orgA) shouldn't see a disabled taxonomy from orgA"),
        ("instructorA", "t2", "User with OrgInstructorRole(orgA) shouldn't see a disabled global taxonomy"),
        ("library_staffA", "tA2", "User with OrgLibraryUserRole(orgA) shouldn't see a disabled taxonomy from orgA"),
        ("library_staffA", "tBA2", "User with OrgLibraryUserRole(orgA) shouldn't see a disabled taxonomy from orgA"),
        ("library_staffA", "t2", "User with OrgInstructorRole(orgA) shouldn't see a disabled global taxonomy"),
        (
            "course_instructorA",
            "tA2",
            "User with CourseInstructorRole in a course from orgA shouldn't see a disabled taxonomy from orgA"
        ),
        (
            "course_instructorA",
            "tBA2",
            "User with CourseInstructorRole in a course from orgA shouldn't see a disabled taxonomy from orgA"
        ),
        (
            "course_instructorA",
            "t2",
            "User with CourseInstructorRole in a course from orgA shouldn't see a disabled global taxonomy"
        ),
        (
            "course_staffA",
            "tA2",
            "User with CourseStaffRole in a course from orgA shouldn't see a disabled taxonomy from orgA"
        ),
        (
            "course_staffA",
            "tBA2",
            "User with CourseStaffRole in a course from orgA shouldn't see a disabled taxonomy from orgA"
        ),
        (
            "course_staffA",
            "t2",
            "User with CourseStaffRole in a course from orgA should't see a disabled global taxonomy"
        ),
        (
            "library_userA",
            "tA2",
            "User with permission on a library from orgA shouldn't see an disabled taxonomy from orgA"
        ),
        (
            "library_userA",
            "tBA2",
            "User with permission on a library from orgA shouldn't see an disabled taxonomy from orgA"
        ),
        (
            "library_userA",
            "t2",
            "User with permission on a library from orgA shouldn't see an disabled global taxonomy"
        ),
    )
    @ddt.unpack
    def test_detail_taxonomy_org_user_dont_see_disabled(self, user_attr: str, taxonomy_attr: str, reason: str) -> None:
        """
        Tests that org users (content creators and instructors) can't see disabled global taxonomies and taxonomies
        from their orgs
        """
        self._test_api_call(
            user_attr=user_attr,
            taxonomy_attr=taxonomy_attr,
            expected_status=status.HTTP_404_NOT_FOUND,
            reason=reason,
        )

    @ddt.data(
        ("staff", "ot1", "Staff should see an enabled no org taxonomy"),
        ("staff", "ot2", "Staff should see a disabled no org taxonomy"),
    )
    @ddt.unpack
    def test_detail_taxonomy_staff_see_no_org(self, user_attr: str, taxonomy_attr: str, reason: str) -> None:
        """
        Tests that staff can see taxonomies with no org
        """
        self._test_api_call(
            user_attr=user_attr,
            taxonomy_attr=taxonomy_attr,
            expected_status=status.HTTP_200_OK,
            reason=reason,
        )

    @ddt.data(
        "staffA",
        "content_creatorA",
        "instructorA",
        "library_staffA",
        "course_instructorA",
        "course_staffA",
        "library_userA"
    )
    def test_detail_taxonomy_other_dont_see_no_org(self, user_attr: str) -> None:
        """
        Tests that org users can't see taxonomies with no org
        """
        self._test_api_call(
            user_attr=user_attr,
            taxonomy_attr="ot1",
            expected_status=status.HTTP_404_NOT_FOUND,
            reason="Only staff should see taxonomies with no org",
        )

    @ddt.data(
        "staffA",
        "content_creatorA",
        "instructorA",
        "library_staffA",
        "course_instructorA",
        "course_staffA",
        "library_userA"
    )
    def test_detail_taxonomy_dont_see_other_org(self, user_attr: str) -> None:
        """
        Tests that org users can't see taxonomies from other orgs
        """
        self._test_api_call(
            user_attr=user_attr,
            taxonomy_attr="tB1",
            expected_status=status.HTTP_404_NOT_FOUND,
            reason="Users shouldn't see taxonomies from other orgs",
        )

    @ddt.data(
        "ot1",
        "ot2",
        "st1",
        "st2",
        "t1",
        "t2",
        "tA1",
        "tA2",
        "tB1",
        "tB2",
        "tBA1",
        "tBA2",
    )
    def test_detail_taxonomy_staff_see_all(self, taxonomy_attr: str) -> None:
        """
        Tests that staff can see all taxonomies
        """
        self._test_api_call(
            user_attr="staff",
            taxonomy_attr=taxonomy_attr,
            expected_status=status.HTTP_200_OK,
            reason="Staff should see all taxonomies",
        )


@skip_unless_cms
class TestTaxonomyDetailViewSet(TestTaxonomyDetailExportMixin, APITestCase):
    """
    Test cases for TaxonomyViewSet with detail action
    """

    def _test_api_call(self, **kwargs) -> None:
        """
        Helper function to call the retrieve endpoint and check the response
        """
        user_attr = kwargs.get("user_attr")
        taxonomy_attr = kwargs.get("taxonomy_attr")
        expected_status = kwargs.get("expected_status")
        reason = kwargs.get("reason", "Unexpected response status")

        assert taxonomy_attr is not None, "taxonomy_attr is required"
        assert user_attr is not None, "user_attr is required"
        assert expected_status is not None, "expected_status is required"

        taxonomy = getattr(self, taxonomy_attr)

        url = TAXONOMY_ORG_DETAIL_URL.format(pk=taxonomy.pk)

        user = getattr(self, user_attr)
        self.client.force_authenticate(user=user)

        response = self.client.get(url)
        assert response.status_code == expected_status, reason

        if status.is_success(expected_status):
            check_taxonomy(response.data, taxonomy.pk, **(TaxonomySerializer(taxonomy.cast()).data))


@skip_unless_cms
class TestTaxonomyExportViewSet(TestTaxonomyDetailExportMixin, APITestCase):
    """
    Test cases for TaxonomyViewSet with export action
    """

    def _test_api_call(self, **kwargs) -> None:
        """
        Helper function to call the export endpoint and check the response
        """
        user_attr = kwargs.get("user_attr")
        taxonomy_attr = kwargs.get("taxonomy_attr")
        expected_status = kwargs.get("expected_status")
        reason = kwargs.get("reason", "Unexpected response status")

        assert taxonomy_attr is not None, "taxonomy_attr is required"
        assert user_attr is not None, "user_attr is required"
        assert expected_status is not None, "expected_status is required"

        taxonomy = getattr(self, taxonomy_attr)

        url = TAXONOMY_ORG_DETAIL_URL.format(pk=taxonomy.pk)

        user = getattr(self, user_attr)
        self.client.force_authenticate(user=user)

        response = self.client.get(url)
        assert response.status_code == expected_status, reason
        assert len(response.data) > 0


@ddt.ddt
class TestTaxonomyChangeMixin(TestTaxonomyObjectsMixin):
    """
    Test cases to be used with update, patch and delete actions
    """

    @abc.abstractmethod
    def _test_api_call(self, **_kwargs) -> None:
        """
        Helper function to call the update/patch/delete endpoint and check the response
        """

    @ddt.data(
        "ot1",
        "ot2",
        "st1",
        "st2",
        "t1",
        "t2",
        "tA1",
        "tA2",
        "tB1",
        "tB2",
        "tBA1",
        "tBA2",
    )
    def test_regular_user_cant_edit_taxonomies(self, taxonomy_attr: str) -> None:
        """
        Tests that regular users can't edit taxonomies
        """
        self._test_api_call(
            user_attr="user",
            taxonomy_attr=taxonomy_attr,
            expected_status=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
            reason="Regular users shouldn't be able to edit taxonomies",
        )

    @ddt.data(
        "content_creatorA",
        "instructorA",
        "library_staffA",
        "course_instructorA",
        "course_staffA",
        "library_userA",
    )
    def test_org_user_cant_edit_org_taxonomies(self, user_attr: str) -> None:
        """
        Tests that content creators and instructors from orgA can't edit taxonomies from orgA
        """
        self._test_api_call(
            user_attr=user_attr,
            taxonomy_attr="tA1",
            expected_status=[status.HTTP_403_FORBIDDEN],
            reason="Content creators and instructors shouldn't be able to edit taxonomies",
        )

    @ddt.data(
        "tA1",
        "tA2",
        "tBA1",
        "tBA2",
    )
    def test_org_staff_can_edit_org_taxonomies(self, taxonomy_attr: str) -> None:
        """
        Tests that org staff can edit taxonomies from their orgs
        """
        self._test_api_call(
            user_attr="staffA",
            taxonomy_attr=taxonomy_attr,
            # Check both status: 200 for update and 204 for delete
            expected_status=[status.HTTP_200_OK, status.HTTP_204_NO_CONTENT],
            reason="Org staff should be able to edit taxonomies from their orgs",
        )

    @ddt.data(
        "tB1",
        "tB2",
    )
    def test_org_staff_cant_edit_other_org_taxonomies(self, taxonomy_attr: str) -> None:
        """
        Tests that org staff can't edit taxonomies from other orgs
        """
        self._test_api_call(
            user_attr="staffA",
            taxonomy_attr=taxonomy_attr,
            expected_status=[status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND],
            reason="Org staff shouldn't be able to edit taxonomies from other orgs",
        )

    @ddt.data(
        "ot1",
        "ot2",
        "t1",
        "t2",
        "tA1",
        "tA2",
        "tB1",
        "tB2",
        "tBA1",
        "tBA2",

    )
    def test_staff_can_edit_almost_all_taxonomies(self, taxonomy_attr: str) -> None:
        """
        Tests that staff can edit all but system defined taxonomies
        """
        self._test_api_call(
            user_attr="staff",
            taxonomy_attr=taxonomy_attr,
            # Check both status: 200 for update and 204 for delete
            expected_status=[status.HTTP_200_OK, status.HTTP_204_NO_CONTENT],
            reason="Staff should be able to edit all but system defined taxonomies",
        )

    @ddt.data(
        "st1",
        "st2",
    )
    def test_staff_cant_edit_system_defined_taxonomies(self, taxonomy_attr: str) -> None:
        """
        Tests that staff can't edit system defined taxonomies
        """
        self._test_api_call(
            user_attr="staff",
            taxonomy_attr=taxonomy_attr,
            # Check both status: 200 for update and 204 for delete
            expected_status=[status.HTTP_403_FORBIDDEN],
            reason="Staff shouldn't be able to edit system defined ",
        )


@skip_unless_cms
class TestTaxonomyUpdateViewSet(TestTaxonomyChangeMixin, APITestCase):
    """
    Test cases for TaxonomyViewSet with PUT method
    """

    def _test_api_call(self, **kwargs) -> None:
        user_attr = kwargs.get("user_attr")
        taxonomy_attr = kwargs.get("taxonomy_attr")
        expected_status = kwargs.get("expected_status")
        reason = kwargs.get("reason", "Unexpected response status")

        assert taxonomy_attr is not None, "taxonomy_attr is required"
        assert user_attr is not None, "user_attr is required"
        assert expected_status is not None, "expected_status is required"

        taxonomy = getattr(self, taxonomy_attr)

        url = TAXONOMY_ORG_DETAIL_URL.format(pk=taxonomy.pk)

        user = getattr(self, user_attr)
        self.client.force_authenticate(user=user)

        response = self.client.put(url, {"name": "new name"}, format="json")
        assert response.status_code in expected_status, reason

        # If we were able to update the taxonomy, check if the name changed
        if status.is_success(response.status_code):
            response = self.client.get(url)
            check_taxonomy(
                response.data,
                response.data["id"],
                **{
                    "name": "new name",
                    "description": taxonomy.description,
                    "enabled": taxonomy.enabled,
                },
            )


@skip_unless_cms
class TestTaxonomyPatchViewSet(TestTaxonomyChangeMixin, APITestCase):
    """
    Test cases for TaxonomyViewSet with PATCH method
    """

    def _test_api_call(self, **kwargs) -> None:
        user_attr = kwargs.get("user_attr")
        taxonomy_attr = kwargs.get("taxonomy_attr")
        expected_status = kwargs.get("expected_status")
        reason = kwargs.get("reason", "Unexpected response status")

        assert taxonomy_attr is not None, "taxonomy_attr is required"
        assert user_attr is not None, "user_attr is required"
        assert expected_status is not None, "expected_status is required"

        taxonomy = getattr(self, taxonomy_attr)

        url = TAXONOMY_ORG_DETAIL_URL.format(pk=taxonomy.pk)

        user = getattr(self, user_attr)
        self.client.force_authenticate(user=user)

        response = self.client.patch(url, {"name": "new name"}, format="json")
        assert response.status_code in expected_status, reason

        # If we were able to patch the taxonomy, check if the name changed
        if status.is_success(response.status_code):
            response = self.client.get(url)
            check_taxonomy(
                response.data,
                response.data["id"],
                **{
                    "name": "new name",
                    "description": taxonomy.description,
                    "enabled": taxonomy.enabled,
                },
            )


@skip_unless_cms
class TestTaxonomyDeleteViewSet(TestTaxonomyChangeMixin, APITestCase):
    """
    Test cases for TaxonomyViewSet with DELETE method
    """

    def _test_api_call(self, **kwargs) -> None:
        user_attr = kwargs.get("user_attr")
        taxonomy_attr = kwargs.get("taxonomy_attr")
        expected_status = kwargs.get("expected_status")
        reason = kwargs.get("reason", "Unexpected response status")

        assert taxonomy_attr is not None, "taxonomy_attr is required"
        assert user_attr is not None, "user_attr is required"
        assert expected_status is not None, "expected_status is required"

        taxonomy = getattr(self, taxonomy_attr)

        url = TAXONOMY_ORG_DETAIL_URL.format(pk=taxonomy.pk)

        user = getattr(self, user_attr)
        self.client.force_authenticate(user=user)

        response = self.client.delete(url)
        assert response.status_code in expected_status, reason

        # If we were able to delete the taxonomy, check that it's really gone
        if status.is_success(response.status_code):
            response = self.client.get(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND


class TestObjectTagMixin(TestTaxonomyObjectsMixin):
    """
    Sets up data for testing ObjectTags.
    """
    def setUp(self):
        """
        Setup the test cases
        """
        super().setUp()
        self.xblockA = BlockUsageLocator(
            course_key=self.courseA,
            block_type='problem',
            block_id='block_id'
        )
        self.xblockB = BlockUsageLocator(
            course_key=self.courseB,
            block_type='problem',
            block_id='block_id'
        )

        self.multiple_taxonomy = Taxonomy.objects.create(name="Multiple Taxonomy", allow_multiple=True)
        self.single_value_taxonomy = Taxonomy.objects.create(name="Required Taxonomy", allow_multiple=False)
        for i in range(20):
            # Valid ObjectTags
            Tag.objects.create(taxonomy=self.tA1, value=f"Tag {i}")
            Tag.objects.create(taxonomy=self.tA2, value=f"Tag {i}")
            Tag.objects.create(taxonomy=self.multiple_taxonomy, value=f"Tag {i}")
            Tag.objects.create(taxonomy=self.single_value_taxonomy, value=f"Tag {i}")

        self.open_taxonomy = Taxonomy.objects.create(name="Enabled Free-Text Taxonomy", allow_free_text=True)

        # Add org permissions to taxonomy
        TaxonomyOrg.objects.create(
            taxonomy=self.multiple_taxonomy,
            org=self.orgA,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )
        TaxonomyOrg.objects.create(
            taxonomy=self.single_value_taxonomy,
            org=self.orgA,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )
        TaxonomyOrg.objects.create(
            taxonomy=self.open_taxonomy,
            org=self.orgA,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )

        add_users(self.staff, CourseStaffRole(self.courseA), self.staffA)


@skip_unless_cms
@ddt.ddt
class TestObjectTagViewSet(TestObjectTagMixin, APITestCase):
    """
    Testing various cases for the ObjectTagView.
    """

    def test_get_tags(self):
        pass

    @ddt.data(
        # userA and userS are staff in courseA and can tag using enabled taxonomies
        ("user", "tA1", ["Tag 1"], status.HTTP_403_FORBIDDEN),
        ("staffA", "tA1", ["Tag 1"], status.HTTP_200_OK),
        ("staff", "tA1", ["Tag 1"], status.HTTP_200_OK),
        ("user", "tA1", [], status.HTTP_403_FORBIDDEN),
        ("staffA", "tA1", [], status.HTTP_200_OK),
        ("staff", "tA1", [], status.HTTP_200_OK),
        ("user", "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_403_FORBIDDEN),
        ("staffA", "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_200_OK),
        ("staff", "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_200_OK),
        ("user", "open_taxonomy", ["tag1"], status.HTTP_403_FORBIDDEN),
        ("staffA", "open_taxonomy", ["tag1"], status.HTTP_200_OK),
        ("staff", "open_taxonomy", ["tag1"], status.HTTP_200_OK),
    )
    @ddt.unpack
    def test_tag_course(self, user_attr, taxonomy_attr, tag_values, expected_status):
        """
        Tests that only staff and org level users can tag courses
        """
        user = getattr(self, user_attr)
        self.client.force_authenticate(user=user)

        taxonomy = getattr(self, taxonomy_attr)

        url = OBJECT_TAG_UPDATE_URL.format(object_id=self.courseA, taxonomy_id=taxonomy.pk)

        response = self.client.put(url, {"tags": tag_values}, format="json")

        assert response.status_code == expected_status
        if status.is_success(expected_status):
            assert len(response.data) == len(tag_values)
            assert set(t["value"] for t in response.data) == set(tag_values)

            # Check that re-fetching the tags returns what we set
            response = self.client.get(url, format="json")
            assert status.is_success(response.status_code)
            assert set(t["value"] for t in response.data) == set(tag_values)

    @ddt.data(
        "staffA",
        "staff",
    )
    def test_tag_course_disabled_taxonomy(self, user_attr):
        """
        Nobody can use disable taxonomies to tag objects
        """
        user = getattr(self, user_attr)
        self.client.force_authenticate(user=user)

        disabled_taxonomy = self.tA2
        assert disabled_taxonomy.enabled is False

        url = OBJECT_TAG_UPDATE_URL.format(object_id=self.courseA, taxonomy_id=disabled_taxonomy.pk)
        response = self.client.put(url, {"tags": ["Tag 1"]}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @ddt.data(
        ("staffA", "tA1"),
        ("staff", "tA1"),
        ("staffA", "multiple_taxonomy"),
        ("staff", "multiple_taxonomy"),
    )
    @ddt.unpack
    def test_tag_course_invalid(self, user_attr, taxonomy_attr):
        """
        Tests that nobody can add invalid tags to a course using a closed taxonomy
        """
        user = getattr(self, user_attr)
        self.client.force_authenticate(user=user)

        taxonomy = getattr(self, taxonomy_attr)

        url = OBJECT_TAG_UPDATE_URL.format(object_id=self.courseA, taxonomy_id=taxonomy.pk)

        response = self.client.put(url, {"tags": ["invalid"]}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @ddt.data(
        # userA and userS are staff in courseA (owner of xblockA) and can tag using any taxonomies
        ("user", "tA1", ["Tag 1"], status.HTTP_403_FORBIDDEN),
        ("staffA", "tA1", ["Tag 1"], status.HTTP_200_OK),
        ("staff", "tA1", ["Tag 1"], status.HTTP_200_OK),
        ("user", "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_403_FORBIDDEN),
        ("staffA", "tA1", [], status.HTTP_200_OK),
        ("staff", "tA1", [], status.HTTP_200_OK),
        ("staffA", "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_200_OK),
        ("staff", "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_200_OK),
        ("user", "open_taxonomy", ["tag1"], status.HTTP_403_FORBIDDEN),
        ("staffA", "open_taxonomy", ["tag1"], status.HTTP_200_OK),
        ("staff", "open_taxonomy", ["tag1"], status.HTTP_200_OK),
    )
    @ddt.unpack
    def test_tag_xblock(self, user_attr, taxonomy_attr, tag_values, expected_status):
        """
        Tests that only staff and org level users can tag xblocks
        """
        user = getattr(self, user_attr)
        self.client.force_authenticate(user=user)

        taxonomy = getattr(self, taxonomy_attr)

        url = OBJECT_TAG_UPDATE_URL.format(object_id=self.xblockA, taxonomy_id=taxonomy.pk)

        response = self.client.put(url, {"tags": tag_values}, format="json")

        assert response.status_code == expected_status
        if status.is_success(expected_status):
            assert len(response.data) == len(tag_values)
            assert set(t["value"] for t in response.data) == set(tag_values)

            # Check that re-fetching the tags returns what we set
            response = self.client.get(url, format="json")
            assert status.is_success(response.status_code)
            assert set(t["value"] for t in response.data) == set(tag_values)

    @ddt.data(
        "staffA",
        "staff",
    )
    def test_tag_xblock_disabled_taxonomy(self, user_attr):
        """
        Tests that nobody can use disabled taxonomies to tag xblocks
        """
        user = getattr(self, user_attr)
        self.client.force_authenticate(user=user)

        disabled_taxonomy = self.tA2
        assert disabled_taxonomy.enabled is False

        url = OBJECT_TAG_UPDATE_URL.format(object_id=self.xblockA, taxonomy_id=disabled_taxonomy.pk)
        response = self.client.put(url, {"tags": ["Tag 1"]}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @ddt.data(
        ("staffA", "tA1"),
        ("staff", "tA1"),
        ("staffA", "multiple_taxonomy"),
        ("staff", "multiple_taxonomy"),
    )
    @ddt.unpack
    def test_tag_xblock_invalid(self, user_attr, taxonomy_attr):
        """
        Tests that staff can't add invalid tags to a xblock using a closed taxonomy
        """
        user = getattr(self, user_attr)
        self.client.force_authenticate(user=user)

        taxonomy = getattr(self, taxonomy_attr)

        url = OBJECT_TAG_UPDATE_URL.format(object_id=self.xblockA, taxonomy_id=taxonomy.pk)

        response = self.client.put(url, {"tags": ["invalid"]}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @ddt.data(
        "courseB",
        "xblockB",
    )
    def test_tag_no_permission(self, objectid_attr):
        """
        Test that a user without access to courseB can't apply tags to it
        """
        self.client.force_authenticate(user=self.staffA)
        object_id = getattr(self, objectid_attr)

        url = OBJECT_TAG_UPDATE_URL.format(object_id=object_id, taxonomy_id=self.tA1.pk)

        response = self.client.put(url, {"tags": ["Tag 1"]}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @ddt.data(
        "courseB",
        "xblockB",
    )
    def test_tag_unauthorized(self, objectid_attr):
        """
        Test that a user without access to courseB can't apply tags to it
        """
        object_id = getattr(self, objectid_attr)

        url = OBJECT_TAG_UPDATE_URL.format(object_id=object_id, taxonomy_id=self.tA1.pk)

        response = self.client.put(url, {"tags": ["Tag 1"]}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@skip_unless_cms
@ddt.ddt
class TestDownloadTemplateView(APITestCase):
    """
    Tests the taxonomy template downloads.
    """
    @ddt.data(
        ("template.csv", "text/csv"),
        ("template.json", "application/json"),
    )
    @ddt.unpack
    def test_download(self, filename, content_type):
        url = TAXONOMY_TEMPLATE_URL.format(filename=filename)
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.headers['Content-Type'] == content_type
        assert response.headers['Content-Disposition'] == f'attachment; filename="{filename}"'
        assert int(response.headers['Content-Length']) > 0

    def test_download_not_found(self):
        url = TAXONOMY_TEMPLATE_URL.format(filename="template.txt")
        response = self.client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_download_method_not_allowed(self):
        url = TAXONOMY_TEMPLATE_URL.format(filename="template.txt")
        response = self.client.post(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
