"""
Tests tagging rest api views
"""

from urllib.parse import parse_qs, urlparse

import ddt
from django.contrib.auth import get_user_model
from django.test.testcases import override_settings
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from openedx_tagging.core.tagging.models import Tag, Taxonomy
from openedx_tagging.core.tagging.models.system_defined import SystemDefinedTaxonomy
from openedx_tagging.core.tagging.rest_api.v1.serializers import TaxonomySerializer
from organizations.models import Organization
from rest_framework import status
from rest_framework.test import APITestCase

from common.djangoapps.student.auth import add_users, update_org_role
from common.djangoapps.student.roles import CourseStaffRole, OrgContentCreatorRole
from openedx.core.djangoapps.content_tagging.models import TaxonomyOrg
from openedx.core.djangolib.testing.utils import skip_unless_cms

User = get_user_model()

TAXONOMY_ORG_LIST_URL = "/api/content_tagging/v1/taxonomies/"
TAXONOMY_ORG_DETAIL_URL = "/api/content_tagging/v1/taxonomies/{pk}/"
OBJECT_TAG_UPDATE_URL = "/api/content_tagging/v1/object_tags/{object_id}/?taxonomy={taxonomy_id}"


def check_taxonomy(
    data,
    pk,
    name,
    description=None,
    enabled=True,
    required=False,
    allow_multiple=False,
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
    assert data["required"] == required
    assert data["allow_multiple"] == allow_multiple
    assert data["allow_free_text"] == allow_free_text
    assert data["system_defined"] == system_defined
    assert data["visible_to_authors"] == visible_to_authors


class TestTaxonomyObjectsMixin:
    """
    Sets up data for testing Content Taxonomies.
    """

    def setUp(self):
        super().setUp()
        self.user = User.objects.create(
            username="user",
            email="user@example.com",
        )
        self.userS = User.objects.create(
            username="staff",
            email="staff@example.com",
            is_staff=True,
        )

        self.orgA = Organization.objects.create(name="Organization A", short_name="orgA")
        self.orgB = Organization.objects.create(name="Organization B", short_name="orgB")
        self.orgX = Organization.objects.create(name="Organization X", short_name="orgX")

        self.userA = User.objects.create(
            username="userA",
            email="userA@example.com",
        )
        update_org_role(self.userS, OrgContentCreatorRole, self.userA, [self.orgA.short_name])

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
            org=self.orgA,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )
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
        self.tC1 = Taxonomy.objects.create(name="tC1", enabled=True)
        TaxonomyOrg.objects.create(
            taxonomy=self.tC1,
            org=self.orgA,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )
        TaxonomyOrg.objects.create(
            taxonomy=self.tC1,
            org=self.orgB,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )
        self.tC2 = Taxonomy.objects.create(name="tC2", enabled=False)
        TaxonomyOrg.objects.create(
            taxonomy=self.tC2,
            org=self.orgA,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )
        TaxonomyOrg.objects.create(
            taxonomy=self.tC2,
            org=self.orgB,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )


@skip_unless_cms
@ddt.ddt
@override_settings(FEATURES={"ENABLE_CREATOR_GROUP": True})
class TestTaxonomyViewSet(TestTaxonomyObjectsMixin, APITestCase):
    """
    Test cases for TaxonomyViewSet when ENABLE_CREATOR_GROUP is True
    """

    @ddt.data(
        ("user", None, None, ("ot1", "st1", "t1", "tA1", "tB1", "tC1")),
        ("userA", None, None, ("ot1", "st1", "t1", "tA1", "tB1", "tC1")),
        ("userS", None, None, ("ot1", "ot2", "st1", "st2", "t1", "t2", "tA1", "tA2", "tB1", "tB2")),
        # Default page_size=10, and so "tC1" and "tC2" appear on the second page
        ("user", True, None, ("ot1", "st1", "t1", "tA1", "tB1", "tC1")),
        ("userA", True, None, ("ot1", "st1", "t1", "tA1", "tB1", "tC1")),
        ("userS", True, None, ("ot1", "st1", "t1", "tA1", "tB1", "tC1")),
        ("user", False, None, ()),
        ("userA", False, None, ()),
        ("userS", False, None, ("ot2", "st2", "t2", "tA2", "tB2", "tC2")),
        ("user", None, "orgA", ("st1", "t1", "tA1", "tC1")),
        ("userA", None, "orgA", ("st1", "t1", "tA1", "tC1")),
        ("userS", None, "orgA", ("st1", "st2", "t1", "t2", "tA1", "tA2", "tC1", "tC2")),
        ("user", True, "orgA", ("st1", "t1", "tA1", "tC1")),
        ("userA", True, "orgA", ("st1", "t1", "tA1", "tC1")),
        ("userS", True, "orgA", ("st1", "t1", "tA1", "tC1")),
        ("user", False, "orgA", ()),
        ("userA", False, "orgA", ()),
        ("userS", False, "orgA", ("st2", "t2", "tA2", "tC2")),
        ("user", None, "orgX", ("st1", "t1")),
        ("userA", None, "orgX", ("st1", "t1")),
        ("userS", None, "orgX", ("st1", "st2", "t1", "t2")),
        ("user", True, "orgX", ("st1", "t1")),
        ("userA", True, "orgX", ("st1", "t1")),
        ("userS", True, "orgX", ("st1", "t1")),
        ("user", False, "orgX", ()),
        ("userA", False, "orgX", ()),
        ("userS", False, "orgX", ("st2", "t2")),
    )
    @ddt.unpack
    def test_list_taxonomy(self, user_attr, enabled_parameter, org_name, expected_taxonomies):
        url = TAXONOMY_ORG_LIST_URL

        if user_attr:
            user = getattr(self, user_attr)
            self.client.force_authenticate(user=user)

        # Set parameters cleaning empty values
        query_params = {k: v for k, v in {"enabled": enabled_parameter, "org": org_name}.items() if v is not None}

        response = self.client.get(url, query_params, format="json")

        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(set(t["name"] for t in response.data["results"]), set(expected_taxonomies))

    def test_list_taxonomy_invalid_org(
        self,
    ):
        url = TAXONOMY_ORG_LIST_URL

        self.client.force_authenticate(user=self.userS)

        # Set parameters cleaning empty values
        query_params = {"org": "invalidOrg"}

        response = self.client.get(url, query_params, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @ddt.data(
        ("user", ("tA1", "tB1", "tC1"), None),
        ("userA", ("tA1", "tB1", "tC1"), None),
        ("userS", ("st2", "t1", "t2"), "3"),
    )
    @ddt.unpack
    def test_list_taxonomy_pagination(self, user_attr, expected_taxonomies, expected_next_page):
        url = TAXONOMY_ORG_LIST_URL

        if user_attr:
            user = getattr(self, user_attr)
            self.client.force_authenticate(user=user)

        query_params = {"page_size": 3, "page": 2}

        response = self.client.get(url, query_params, format="json")

        assert response.status_code == status.HTTP_200_OK
        self.assertEqual(set(t["name"] for t in response.data["results"]), set(expected_taxonomies))
        parsed_url = urlparse(response.data["next"])

        next_page = parse_qs(parsed_url.query).get("page", [None])[0]
        assert next_page == expected_next_page

    def test_list_invalid_page(self):
        url = TAXONOMY_ORG_LIST_URL

        self.client.force_authenticate(user=self.user)

        query_params = {"page": 123123}

        response = self.client.get(url, query_params, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @ddt.data(
        (None, "ot1", status.HTTP_403_FORBIDDEN),
        (None, "ot2", status.HTTP_403_FORBIDDEN),
        (None, "st1", status.HTTP_403_FORBIDDEN),
        (None, "st2", status.HTTP_403_FORBIDDEN),
        (None, "t1", status.HTTP_403_FORBIDDEN),
        (None, "t2", status.HTTP_403_FORBIDDEN),
        (None, "tA1", status.HTTP_403_FORBIDDEN),
        (None, "tA2", status.HTTP_403_FORBIDDEN),
        (None, "tB1", status.HTTP_403_FORBIDDEN),
        (None, "tB2", status.HTTP_403_FORBIDDEN),
        (None, "tC1", status.HTTP_403_FORBIDDEN),
        (None, "tC2", status.HTTP_403_FORBIDDEN),
        ("user", "ot1", status.HTTP_200_OK),
        ("user", "ot2", status.HTTP_404_NOT_FOUND),
        ("user", "st1", status.HTTP_200_OK),
        ("user", "st2", status.HTTP_404_NOT_FOUND),
        ("user", "t1", status.HTTP_200_OK),
        ("user", "t2", status.HTTP_404_NOT_FOUND),
        ("user", "tA1", status.HTTP_200_OK),
        ("user", "tA2", status.HTTP_404_NOT_FOUND),
        ("user", "tB1", status.HTTP_200_OK),
        ("user", "tB2", status.HTTP_404_NOT_FOUND),
        ("user", "tC1", status.HTTP_200_OK),
        ("user", "tC2", status.HTTP_404_NOT_FOUND),
        ("userA", "ot1", status.HTTP_200_OK),
        ("userA", "ot2", status.HTTP_404_NOT_FOUND),
        ("userA", "st1", status.HTTP_200_OK),
        ("userA", "st2", status.HTTP_404_NOT_FOUND),
        ("userA", "t1", status.HTTP_200_OK),
        ("userA", "t2", status.HTTP_404_NOT_FOUND),
        ("userA", "tA1", status.HTTP_200_OK),
        ("userA", "tA2", status.HTTP_404_NOT_FOUND),
        ("userA", "tB1", status.HTTP_200_OK),
        ("userA", "tB2", status.HTTP_404_NOT_FOUND),
        ("userA", "tC1", status.HTTP_200_OK),
        ("userA", "tC2", status.HTTP_404_NOT_FOUND),
        ("userS", "ot1", status.HTTP_200_OK),
        ("userS", "ot2", status.HTTP_200_OK),
        ("userS", "st1", status.HTTP_200_OK),
        ("userS", "st2", status.HTTP_200_OK),
        ("userS", "t1", status.HTTP_200_OK),
        ("userS", "t2", status.HTTP_200_OK),
        ("userS", "tA1", status.HTTP_200_OK),
        ("userS", "tA2", status.HTTP_200_OK),
        ("userS", "tB1", status.HTTP_200_OK),
        ("userS", "tB2", status.HTTP_200_OK),
        ("userS", "tC1", status.HTTP_200_OK),
        ("userS", "tC2", status.HTTP_200_OK),
    )
    @ddt.unpack
    def test_detail_taxonomy(self, user_attr, taxonomy_attr, expected_status):
        taxonomy = getattr(self, taxonomy_attr)

        url = TAXONOMY_ORG_DETAIL_URL.format(pk=taxonomy.pk)

        if user_attr:
            user = getattr(self, user_attr)
            self.client.force_authenticate(user=user)

        response = self.client.get(url)
        assert response.status_code == expected_status

        if status.is_success(expected_status):
            check_taxonomy(response.data, taxonomy.pk, **(TaxonomySerializer(taxonomy.cast()).data))

    @ddt.data(
        (None, status.HTTP_403_FORBIDDEN),
        ("user", status.HTTP_403_FORBIDDEN),
        ("userA", status.HTTP_403_FORBIDDEN),
        ("userS", status.HTTP_201_CREATED),
    )
    @ddt.unpack
    def test_create_taxonomy(self, user_attr, expected_status):
        url = TAXONOMY_ORG_LIST_URL

        create_data = {
            "name": "taxonomy_data",
            "description": "This is a description",
            "enabled": True,
            "required": True,
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

    @ddt.data(
        (None, "ot1", status.HTTP_403_FORBIDDEN),
        (None, "ot2", status.HTTP_403_FORBIDDEN),
        (None, "st1", status.HTTP_403_FORBIDDEN),
        (None, "st2", status.HTTP_403_FORBIDDEN),
        (None, "t1", status.HTTP_403_FORBIDDEN),
        (None, "t2", status.HTTP_403_FORBIDDEN),
        (None, "tA1", status.HTTP_403_FORBIDDEN),
        (None, "tA2", status.HTTP_403_FORBIDDEN),
        (None, "tB1", status.HTTP_403_FORBIDDEN),
        (None, "tB2", status.HTTP_403_FORBIDDEN),
        (None, "tC1", status.HTTP_403_FORBIDDEN),
        (None, "tC2", status.HTTP_403_FORBIDDEN),
        ("user", "ot1", status.HTTP_403_FORBIDDEN),
        ("user", "ot2", status.HTTP_403_FORBIDDEN),
        ("user", "st1", status.HTTP_403_FORBIDDEN),
        ("user", "st2", status.HTTP_403_FORBIDDEN),
        ("user", "t1", status.HTTP_403_FORBIDDEN),
        ("user", "t2", status.HTTP_403_FORBIDDEN),
        ("user", "tA1", status.HTTP_403_FORBIDDEN),
        ("user", "tA2", status.HTTP_403_FORBIDDEN),
        ("user", "tB1", status.HTTP_403_FORBIDDEN),
        ("user", "tB2", status.HTTP_403_FORBIDDEN),
        ("user", "tC1", status.HTTP_403_FORBIDDEN),
        ("user", "tC2", status.HTTP_403_FORBIDDEN),
        ("userA", "ot1", status.HTTP_403_FORBIDDEN),
        ("userA", "ot2", status.HTTP_403_FORBIDDEN),
        ("userA", "st1", status.HTTP_403_FORBIDDEN),
        ("userA", "st2", status.HTTP_403_FORBIDDEN),
        ("userA", "t1", status.HTTP_403_FORBIDDEN),
        ("userA", "t2", status.HTTP_403_FORBIDDEN),
        ("userA", "tA1", status.HTTP_403_FORBIDDEN),
        ("userA", "tA2", status.HTTP_403_FORBIDDEN),
        ("userA", "tB1", status.HTTP_403_FORBIDDEN),
        ("userA", "tB2", status.HTTP_403_FORBIDDEN),
        ("userA", "tC1", status.HTTP_403_FORBIDDEN),
        ("userA", "tC2", status.HTTP_403_FORBIDDEN),
        ("userS", "ot1", status.HTTP_200_OK),
        ("userS", "ot2", status.HTTP_200_OK),
        ("userS", "st1", status.HTTP_403_FORBIDDEN),
        ("userS", "st2", status.HTTP_403_FORBIDDEN),
        ("userS", "t1", status.HTTP_200_OK),
        ("userS", "t2", status.HTTP_200_OK),
        ("userS", "t1", status.HTTP_200_OK),
        ("userS", "t2", status.HTTP_200_OK),
        ("userS", "tA1", status.HTTP_200_OK),
        ("userS", "tA2", status.HTTP_200_OK),
        ("userS", "tB1", status.HTTP_200_OK),
        ("userS", "tB2", status.HTTP_200_OK),
        ("userS", "tC1", status.HTTP_200_OK),
        ("userS", "tC2", status.HTTP_200_OK),
    )
    @ddt.unpack
    def test_update_taxonomy(self, user_attr, taxonomy_attr, expected_status):
        taxonomy = getattr(self, taxonomy_attr)

        url = TAXONOMY_ORG_DETAIL_URL.format(pk=taxonomy.pk)

        if user_attr:
            user = getattr(self, user_attr)
            self.client.force_authenticate(user=user)

        response = self.client.put(url, {"name": "new name"}, format="json")
        assert response.status_code == expected_status

        # If we were able to update the taxonomy, check if the name changed
        if status.is_success(expected_status):
            response = self.client.get(url)
            check_taxonomy(
                response.data,
                response.data["id"],
                **{
                    "name": "new name",
                    "description": taxonomy.description,
                    "enabled": taxonomy.enabled,
                    "required": taxonomy.required,
                },
            )

    @ddt.data(
        (False, status.HTTP_403_FORBIDDEN),
        (True, status.HTTP_403_FORBIDDEN),
    )
    @ddt.unpack
    def test_update_taxonomy_system_defined(self, update_value, expected_status):
        """
        Test that we can't update system_defined field
        """
        url = TAXONOMY_ORG_DETAIL_URL.format(pk=self.st1.pk)

        self.client.force_authenticate(user=self.userS)
        response = self.client.put(url, {"name": "new name", "system_defined": update_value}, format="json")
        assert response.status_code == expected_status

        # Verify that system_defined has not changed
        response = self.client.get(url)
        assert response.data["system_defined"] is True

    @ddt.data(
        (None, "ot1", status.HTTP_403_FORBIDDEN),
        (None, "ot2", status.HTTP_403_FORBIDDEN),
        (None, "st1", status.HTTP_403_FORBIDDEN),
        (None, "st2", status.HTTP_403_FORBIDDEN),
        (None, "t1", status.HTTP_403_FORBIDDEN),
        (None, "t2", status.HTTP_403_FORBIDDEN),
        (None, "tA1", status.HTTP_403_FORBIDDEN),
        (None, "tA2", status.HTTP_403_FORBIDDEN),
        (None, "tB1", status.HTTP_403_FORBIDDEN),
        (None, "tB2", status.HTTP_403_FORBIDDEN),
        (None, "tC1", status.HTTP_403_FORBIDDEN),
        (None, "tC2", status.HTTP_403_FORBIDDEN),
        ("user", "ot1", status.HTTP_403_FORBIDDEN),
        ("user", "ot2", status.HTTP_403_FORBIDDEN),
        ("user", "st1", status.HTTP_403_FORBIDDEN),
        ("user", "st2", status.HTTP_403_FORBIDDEN),
        ("user", "t1", status.HTTP_403_FORBIDDEN),
        ("user", "t2", status.HTTP_403_FORBIDDEN),
        ("user", "tA1", status.HTTP_403_FORBIDDEN),
        ("user", "tA2", status.HTTP_403_FORBIDDEN),
        ("user", "tB1", status.HTTP_403_FORBIDDEN),
        ("user", "tB2", status.HTTP_403_FORBIDDEN),
        ("user", "tC1", status.HTTP_403_FORBIDDEN),
        ("user", "tC2", status.HTTP_403_FORBIDDEN),
        ("userA", "ot1", status.HTTP_403_FORBIDDEN),
        ("userA", "ot2", status.HTTP_403_FORBIDDEN),
        ("userA", "st1", status.HTTP_403_FORBIDDEN),
        ("userA", "st2", status.HTTP_403_FORBIDDEN),
        ("userA", "t1", status.HTTP_403_FORBIDDEN),
        ("userA", "t2", status.HTTP_403_FORBIDDEN),
        ("userA", "tA1", status.HTTP_403_FORBIDDEN),
        ("userA", "tA2", status.HTTP_403_FORBIDDEN),
        ("userA", "tB1", status.HTTP_403_FORBIDDEN),
        ("userA", "tB2", status.HTTP_403_FORBIDDEN),
        ("userA", "tC1", status.HTTP_403_FORBIDDEN),
        ("userA", "tC2", status.HTTP_403_FORBIDDEN),
        ("userS", "ot1", status.HTTP_200_OK),
        ("userS", "ot2", status.HTTP_200_OK),
        ("userS", "st1", status.HTTP_403_FORBIDDEN),
        ("userS", "st2", status.HTTP_403_FORBIDDEN),
        ("userS", "t1", status.HTTP_200_OK),
        ("userS", "t2", status.HTTP_200_OK),
        ("userS", "tA1", status.HTTP_200_OK),
        ("userS", "tA2", status.HTTP_200_OK),
        ("userS", "tB1", status.HTTP_200_OK),
        ("userS", "tB2", status.HTTP_200_OK),
        ("userS", "tC1", status.HTTP_200_OK),
        ("userS", "tC2", status.HTTP_200_OK),
    )
    @ddt.unpack
    def test_patch_taxonomy(self, user_attr, taxonomy_attr, expected_status):
        taxonomy = getattr(self, taxonomy_attr)

        url = TAXONOMY_ORG_DETAIL_URL.format(pk=taxonomy.pk)

        if user_attr:
            user = getattr(self, user_attr)
            self.client.force_authenticate(user=user)

        response = self.client.patch(url, {"name": "new name"}, format="json")
        assert response.status_code == expected_status

        # If we were able to patch the taxonomy, check if the name changed
        if status.is_success(expected_status):
            response = self.client.get(url)
            check_taxonomy(
                response.data,
                response.data["id"],
                **{
                    "name": "new name",
                    "description": taxonomy.description,
                    "enabled": taxonomy.enabled,
                    "required": taxonomy.required,
                },
            )

    @ddt.data(
        (False, status.HTTP_403_FORBIDDEN),
        (True, status.HTTP_403_FORBIDDEN),
    )
    @ddt.unpack
    def test_patch_taxonomy_system_defined(self, update_value, expected_status):
        """
        Test that we can't patch system_defined field
        """
        url = TAXONOMY_ORG_DETAIL_URL.format(pk=self.st1.pk)

        self.client.force_authenticate(user=self.userS)
        response = self.client.patch(url, {"name": "new name", "system_defined": update_value}, format="json")
        assert response.status_code == expected_status

        # Verify that system_defined has not changed
        response = self.client.get(url)
        assert response.data["system_defined"] is True

    @ddt.data(
        (None, "ot1", status.HTTP_403_FORBIDDEN),
        (None, "ot2", status.HTTP_403_FORBIDDEN),
        (None, "st1", status.HTTP_403_FORBIDDEN),
        (None, "st2", status.HTTP_403_FORBIDDEN),
        (None, "t1", status.HTTP_403_FORBIDDEN),
        (None, "t2", status.HTTP_403_FORBIDDEN),
        (None, "tA1", status.HTTP_403_FORBIDDEN),
        (None, "tA2", status.HTTP_403_FORBIDDEN),
        (None, "tB1", status.HTTP_403_FORBIDDEN),
        (None, "tB2", status.HTTP_403_FORBIDDEN),
        (None, "tC1", status.HTTP_403_FORBIDDEN),
        (None, "tC2", status.HTTP_403_FORBIDDEN),
        ("user", "ot1", status.HTTP_403_FORBIDDEN),
        ("user", "ot2", status.HTTP_403_FORBIDDEN),
        ("user", "st1", status.HTTP_403_FORBIDDEN),
        ("user", "st2", status.HTTP_403_FORBIDDEN),
        ("user", "t1", status.HTTP_403_FORBIDDEN),
        ("user", "t2", status.HTTP_403_FORBIDDEN),
        ("user", "tA1", status.HTTP_403_FORBIDDEN),
        ("user", "tA2", status.HTTP_403_FORBIDDEN),
        ("user", "tB1", status.HTTP_403_FORBIDDEN),
        ("user", "tB2", status.HTTP_403_FORBIDDEN),
        ("user", "tC1", status.HTTP_403_FORBIDDEN),
        ("user", "tC2", status.HTTP_403_FORBIDDEN),
        ("userA", "ot1", status.HTTP_403_FORBIDDEN),
        ("userA", "ot2", status.HTTP_403_FORBIDDEN),
        ("userA", "st1", status.HTTP_403_FORBIDDEN),
        ("userA", "st2", status.HTTP_403_FORBIDDEN),
        ("userA", "t1", status.HTTP_403_FORBIDDEN),
        ("userA", "t2", status.HTTP_403_FORBIDDEN),
        ("userA", "tA1", status.HTTP_403_FORBIDDEN),
        ("userA", "tA2", status.HTTP_403_FORBIDDEN),
        ("userA", "tB1", status.HTTP_403_FORBIDDEN),
        ("userA", "tB2", status.HTTP_403_FORBIDDEN),
        ("userA", "tC1", status.HTTP_403_FORBIDDEN),
        ("userA", "tC2", status.HTTP_403_FORBIDDEN),
        ("userS", "ot1", status.HTTP_204_NO_CONTENT),
        ("userS", "ot2", status.HTTP_204_NO_CONTENT),
        ("userS", "st1", status.HTTP_403_FORBIDDEN),
        ("userS", "st2", status.HTTP_403_FORBIDDEN),
        ("userS", "t1", status.HTTP_204_NO_CONTENT),
        ("userS", "t2", status.HTTP_204_NO_CONTENT),
        ("userS", "tA1", status.HTTP_204_NO_CONTENT),
        ("userS", "tA2", status.HTTP_204_NO_CONTENT),
        ("userS", "tB1", status.HTTP_204_NO_CONTENT),
        ("userS", "tB2", status.HTTP_204_NO_CONTENT),
        ("userS", "tC1", status.HTTP_204_NO_CONTENT),
        ("userS", "tC2", status.HTTP_204_NO_CONTENT),
    )
    @ddt.unpack
    def test_delete_taxonomy(self, user_attr, taxonomy_attr, expected_status):
        taxonomy = getattr(self, taxonomy_attr)

        url = TAXONOMY_ORG_DETAIL_URL.format(pk=taxonomy.pk)

        if user_attr:
            user = getattr(self, user_attr)
            self.client.force_authenticate(user=user)

        response = self.client.delete(url)
        assert response.status_code == expected_status

        # If we were able to delete the taxonomy, check that it's really gone
        if status.is_success(expected_status):
            response = self.client.get(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND


@skip_unless_cms
@ddt.ddt
@override_settings(FEATURES={"ENABLE_CREATOR_GROUP": False})
class TestTaxonomyViewSetNoCreatorGroup(TestTaxonomyViewSet):  # pylint: disable=test-inherits-tests
    """
    Test cases for TaxonomyViewSet when ENABLE_CREATOR_GROUP is False

    The permissions are the same for when ENABLED_CREATOR_GRUP is True
    """


@skip_unless_cms
@ddt.ddt
class TestObjectTagViewSet(TestTaxonomyObjectsMixin, APITestCase):
    """
    Testing various cases for the ObjectTagView.
    """
    def setUp(self):
        """
        Setup the test cases
        """
        super().setUp()
        self.courseA = CourseLocator("orgA", "101", "test")
        self.xblockA = BlockUsageLocator(
            course_key=self.courseA,
            block_type='problem',
            block_id='block_id'
        )
        self.courseB = CourseLocator("orgB", "101", "test")
        self.xblockB = BlockUsageLocator(
            course_key=self.courseB,
            block_type='problem',
            block_id='block_id'
        )

        self.multiple_taxonomy = Taxonomy.objects.create(name="Multiple Taxonomy", allow_multiple=True)
        self.required_taxonomy = Taxonomy.objects.create(name="Required Taxonomy", required=True)
        for i in range(20):
            # Valid ObjectTags
            Tag.objects.create(taxonomy=self.tA1, value=f"Tag {i}")
            Tag.objects.create(taxonomy=self.tA2, value=f"Tag {i}")
            Tag.objects.create(taxonomy=self.multiple_taxonomy, value=f"Tag {i}")
            Tag.objects.create(taxonomy=self.required_taxonomy, value=f"Tag {i}")

        self.open_taxonomy = Taxonomy.objects.create(name="Enabled Free-Text Taxonomy", allow_free_text=True)

        # Add org permissions to taxonomy
        TaxonomyOrg.objects.create(
            taxonomy=self.multiple_taxonomy,
            org=self.orgA,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )
        TaxonomyOrg.objects.create(
            taxonomy=self.required_taxonomy,
            org=self.orgA,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )
        TaxonomyOrg.objects.create(
            taxonomy=self.open_taxonomy,
            org=self.orgA,
            rel_type=TaxonomyOrg.RelType.OWNER,
        )

        add_users(self.userS, CourseStaffRole(self.courseA), self.userA)

    @ddt.data(
        # userA and userS are staff in courseA and can tag using enabled taxonomies
        (None, "tA1", ["Tag 1"], status.HTTP_403_FORBIDDEN),
        ("user", "tA1", ["Tag 1"], status.HTTP_403_FORBIDDEN),
        ("userA", "tA1", ["Tag 1"], status.HTTP_200_OK),
        ("userS", "tA1", ["Tag 1"], status.HTTP_200_OK),
        (None, "tA1", [], status.HTTP_403_FORBIDDEN),
        ("user", "tA1", [], status.HTTP_403_FORBIDDEN),
        ("userA", "tA1", [], status.HTTP_200_OK),
        ("userS", "tA1", [], status.HTTP_200_OK),
        (None, "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_403_FORBIDDEN),
        ("user", "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_403_FORBIDDEN),
        ("userA", "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_200_OK),
        ("userS", "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_200_OK),
        (None, "open_taxonomy", ["tag1"], status.HTTP_403_FORBIDDEN),
        ("user", "open_taxonomy", ["tag1"], status.HTTP_403_FORBIDDEN),
        ("userA", "open_taxonomy", ["tag1"], status.HTTP_200_OK),
        ("userS", "open_taxonomy", ["tag1"], status.HTTP_200_OK),
        # Only userS is Tagging Admin and can tag objects using disabled taxonomies
        (None, "tA2", ["Tag 1"], status.HTTP_403_FORBIDDEN),
        ("user", "tA2", ["Tag 1"], status.HTTP_403_FORBIDDEN),
        ("userA", "tA2", ["Tag 1"], status.HTTP_403_FORBIDDEN),
        ("userS", "tA2", ["Tag 1"], status.HTTP_200_OK),
    )
    @ddt.unpack
    def test_tag_course(self, user_attr, taxonomy_attr, tag_values, expected_status):
        if user_attr:
            user = getattr(self, user_attr)
            self.client.force_authenticate(user=user)

        taxonomy = getattr(self, taxonomy_attr)

        url = OBJECT_TAG_UPDATE_URL.format(object_id=self.courseA, taxonomy_id=taxonomy.pk)

        response = self.client.put(url, {"tags": tag_values}, format="json")

        assert response.status_code == expected_status
        if status.is_success(expected_status):
            assert len(response.data) == len(tag_values)
            assert set(t["value"] for t in response.data) == set(tag_values)

    @ddt.data(
        # Can't add invalid tags to a object using a closed taxonomy
        (None, "tA1", ["invalid"], status.HTTP_403_FORBIDDEN),
        ("user", "tA1", ["invalid"], status.HTTP_403_FORBIDDEN),
        ("userA", "tA1", ["invalid"], status.HTTP_400_BAD_REQUEST),
        ("userS", "tA1", ["invalid"], status.HTTP_400_BAD_REQUEST),
        (None, "multiple_taxonomy", ["invalid"], status.HTTP_403_FORBIDDEN),
        ("user", "multiple_taxonomy", ["invalid"], status.HTTP_403_FORBIDDEN),
        ("userA", "multiple_taxonomy", ["invalid"], status.HTTP_400_BAD_REQUEST),
        ("userS", "multiple_taxonomy", ["invalid"], status.HTTP_400_BAD_REQUEST),
        # Staff can't add invalid tags to a object using a closed taxonomy
        ("userS", "tA2", ["invalid"], status.HTTP_400_BAD_REQUEST),
    )
    @ddt.unpack
    def test_tag_course_invalid(self, user_attr, taxonomy_attr, tag_values, expected_status):
        if user_attr:
            user = getattr(self, user_attr)
            self.client.force_authenticate(user=user)

        taxonomy = getattr(self, taxonomy_attr)

        url = OBJECT_TAG_UPDATE_URL.format(object_id=self.courseA, taxonomy_id=taxonomy.pk)

        response = self.client.put(url, {"tags": tag_values}, format="json")
        assert response.status_code == expected_status
        assert not status.is_success(expected_status)  # No success cases here

    @ddt.data(
        # userA and userS are staff in courseA (owner of xblockA) and can tag using enabled taxonomies
        (None, "tA1", ["Tag 1"], status.HTTP_403_FORBIDDEN),
        ("user", "tA1", ["Tag 1"], status.HTTP_403_FORBIDDEN),
        ("userA", "tA1", ["Tag 1"], status.HTTP_200_OK),
        ("userS", "tA1", ["Tag 1"], status.HTTP_200_OK),
        (None, "tA1", [], status.HTTP_403_FORBIDDEN),
        ("user", "tA1", [], status.HTTP_403_FORBIDDEN),
        ("userA", "tA1", [], status.HTTP_200_OK),
        ("userS", "tA1", [], status.HTTP_200_OK),
        (None, "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_403_FORBIDDEN),
        ("user", "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_403_FORBIDDEN),
        ("userA", "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_200_OK),
        ("userS", "multiple_taxonomy", ["Tag 1", "Tag 2"], status.HTTP_200_OK),
        (None, "open_taxonomy", ["tag1"], status.HTTP_403_FORBIDDEN),
        ("user", "open_taxonomy", ["tag1"], status.HTTP_403_FORBIDDEN),
        ("userA", "open_taxonomy", ["tag1"], status.HTTP_200_OK),
        ("userS", "open_taxonomy", ["tag1"], status.HTTP_200_OK),
        # Only userS is Tagging Admin and can tag objects using disabled taxonomies
        (None, "tA2", ["Tag 1"], status.HTTP_403_FORBIDDEN),
        ("user", "tA2", ["Tag 1"], status.HTTP_403_FORBIDDEN),
        ("userA", "tA2", ["Tag 1"], status.HTTP_403_FORBIDDEN),
        ("userS", "tA2", ["Tag 1"], status.HTTP_200_OK),
    )
    @ddt.unpack
    def test_tag_xblock(self, user_attr, taxonomy_attr, tag_values, expected_status):
        if user_attr:
            user = getattr(self, user_attr)
            self.client.force_authenticate(user=user)

        taxonomy = getattr(self, taxonomy_attr)

        url = OBJECT_TAG_UPDATE_URL.format(object_id=self.xblockA, taxonomy_id=taxonomy.pk)

        response = self.client.put(url, {"tags": tag_values}, format="json")

        assert response.status_code == expected_status
        if status.is_success(expected_status):
            assert len(response.data) == len(tag_values)
            assert set(t["value"] for t in response.data) == set(tag_values)

    @ddt.data(
        # Can't add invalid tags to a object using a closed taxonomy
        (None, "tA1", ["invalid"], status.HTTP_403_FORBIDDEN),
        ("user", "tA1", ["invalid"], status.HTTP_403_FORBIDDEN),
        ("userA", "tA1", ["invalid"], status.HTTP_400_BAD_REQUEST),
        ("userS", "tA1", ["invalid"], status.HTTP_400_BAD_REQUEST),
        (None, "multiple_taxonomy", ["invalid"], status.HTTP_403_FORBIDDEN),
        ("user", "multiple_taxonomy", ["invalid"], status.HTTP_403_FORBIDDEN),
        ("userA", "multiple_taxonomy", ["invalid"], status.HTTP_400_BAD_REQUEST),
        ("userS", "multiple_taxonomy", ["invalid"], status.HTTP_400_BAD_REQUEST),
        # Staff can't add invalid tags to a object using a closed taxonomy
        ("userS", "tA2", ["invalid"], status.HTTP_400_BAD_REQUEST),
    )
    @ddt.unpack
    def test_tag_xblock_invalid(self, user_attr, taxonomy_attr, tag_values, expected_status):
        if user_attr:
            user = getattr(self, user_attr)
            self.client.force_authenticate(user=user)

        taxonomy = getattr(self, taxonomy_attr)

        url = OBJECT_TAG_UPDATE_URL.format(object_id=self.xblockA, taxonomy_id=taxonomy.pk)

        response = self.client.put(url, {"tags": tag_values}, format="json")
        assert response.status_code == expected_status
        assert not status.is_success(expected_status)  # No success cases here

    @ddt.data(
        "courseB",
        "xblockB",
    )
    def test_tag_unauthorized(self, objectid_attr):
        """
        Test that a user without access to courseB can't apply tags to it
        """
        self.client.force_authenticate(user=self.userA)
        object_id = getattr(self, objectid_attr)

        url = OBJECT_TAG_UPDATE_URL.format(object_id=object_id, taxonomy_id=self.tA1.pk)

        response = self.client.put(url, {"tags": ["Tag 1"]}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
