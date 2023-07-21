"""Tests content_tagging rules-based permissions"""

import ddt
from django.contrib.auth import get_user_model
from django.test.testcases import TestCase, override_settings
from openedx_tagging.core.tagging.models import (
    ObjectTag,
    Tag,
    UserSystemDefinedTaxonomy,
)
from organizations.models import Organization

from common.djangoapps.student.auth import add_users, update_org_role
from common.djangoapps.student.roles import CourseCreatorRole, OrgContentCreatorRole

from .. import api
from .test_api import TestTaxonomyMixin

User = get_user_model()


@ddt.ddt
@override_settings(FEATURES={"ENABLE_CREATOR_GROUP": True})
class TestRulesTaxonomy(TestTaxonomyMixin, TestCase):
    """
    Tests that the expected rules have been applied to the Taxonomy models.

    We set ENABLE_CREATOR_GROUP for these tests, otherwise all users have course creator access for all orgs.
    """

    def setUp(self):
        super().setUp()
        self.superuser = User.objects.create(
            username="superuser",
            email="superuser@example.com",
            is_superuser=True,
        )
        self.staff = User.objects.create(
            username="staff",
            email="staff@example.com",
            is_staff=True,
        )
        # Normal user: grant course creator role (for all orgs)
        self.user_all_orgs = User.objects.create(
            username="user_all_orgs",
            email="staff+all@example.com",
        )
        add_users(self.staff, CourseCreatorRole(), self.user_all_orgs)

        # Normal user: grant course creator access to both org1 and org2
        self.user_both_orgs = User.objects.create(
            username="user_both_orgs",
            email="staff+both@example.com",
        )
        update_org_role(
            self.staff,
            OrgContentCreatorRole,
            self.user_both_orgs,
            [self.org1.short_name, self.org2.short_name],
        )

        # Normal user: grant course creator access to org2
        self.user_org2 = User.objects.create(
            username="user_org2",
            email="staff+org2@example.com",
        )
        update_org_role(
            self.staff, OrgContentCreatorRole, self.user_org2, [self.org2.short_name]
        )

        # Normal user: no course creator access
        self.learner = User.objects.create(
            username="learner",
            email="learner@example.com",
        )

    def _expected_users_have_perm(
        self, perm, obj, learner_perm=False, learner_obj=False, user_org2=True
    ):
        """
        Checks that all users have the given permission on the given object.

        If learners_too, then the learner user should have it too.
        """
        # Global Taxonomy Admins can do pretty much anything
        assert self.superuser.has_perm(perm)
        assert self.superuser.has_perm(perm, obj)
        assert self.staff.has_perm(perm)
        assert self.staff.has_perm(perm, obj)
        assert self.user_all_orgs.has_perm(perm)
        assert self.user_all_orgs.has_perm(perm, obj)

        # Org content creators are bound by a taxonomy's org restrictions
        assert self.user_both_orgs.has_perm(perm) == learner_perm
        assert self.user_both_orgs.has_perm(perm, obj)
        assert self.user_org2.has_perm(perm) == learner_perm
        # user_org2 does not have course creator access for org 1
        assert self.user_org2.has_perm(perm, obj) == user_org2

        # Learners can't do much but view
        assert self.learner.has_perm(perm) == learner_perm
        assert self.learner.has_perm(perm, obj) == learner_obj

    # Taxonomy

    @ddt.data(
        ("oel_tagging.add_taxonomy", "taxonomy_all_orgs"),
        ("oel_tagging.add_taxonomy", "taxonomy_both_orgs"),
        ("oel_tagging.add_taxonomy", "taxonomy_disabled"),
        ("oel_tagging.change_taxonomy", "taxonomy_all_orgs"),
        ("oel_tagging.change_taxonomy", "taxonomy_both_orgs"),
        ("oel_tagging.change_taxonomy", "taxonomy_disabled"),
        ("oel_tagging.delete_taxonomy", "taxonomy_all_orgs"),
        ("oel_tagging.delete_taxonomy", "taxonomy_both_orgs"),
        ("oel_tagging.delete_taxonomy", "taxonomy_disabled"),
    )
    @ddt.unpack
    def test_change_taxonomy_all_orgs(self, perm, taxonomy_attr):
        """Taxonomy administrators with course creator access for the taxonomy org"""
        taxonomy = getattr(self, taxonomy_attr)
        self._expected_users_have_perm(perm, taxonomy)

    @ddt.data(
        ("oel_tagging.add_taxonomy", "taxonomy_one_org"),
        ("oel_tagging.change_taxonomy", "taxonomy_one_org"),
        ("oel_tagging.delete_taxonomy", "taxonomy_one_org"),
    )
    @ddt.unpack
    def test_change_taxonomy_org1(self, perm, taxonomy_attr):
        taxonomy = getattr(self, taxonomy_attr)
        self._expected_users_have_perm(perm, taxonomy, user_org2=False)

    @ddt.data(
        "oel_tagging.add_taxonomy",
        "oel_tagging.change_taxonomy",
        "oel_tagging.delete_taxonomy",
    )
    def test_system_taxonomy(self, perm):
        """Taxonomy administrators cannot edit system taxonomies"""
        system_taxonomy = api.create_taxonomy(
            name="System Languages",
        )
        system_taxonomy.taxonomy_class = UserSystemDefinedTaxonomy
        system_taxonomy = system_taxonomy.cast()
        assert self.superuser.has_perm(perm, system_taxonomy)
        assert not self.staff.has_perm(perm, system_taxonomy)
        assert not self.user_all_orgs.has_perm(perm, system_taxonomy)
        assert not self.user_both_orgs.has_perm(perm, system_taxonomy)
        assert not self.user_org2.has_perm(perm, system_taxonomy)
        assert not self.learner.has_perm(perm, system_taxonomy)

    @ddt.data(
        (True, "taxonomy_all_orgs"),
        (False, "taxonomy_all_orgs"),
        (True, "taxonomy_both_orgs"),
        (False, "taxonomy_both_orgs"),
    )
    @ddt.unpack
    def test_view_taxonomy_enabled(self, enabled, taxonomy_attr):
        """Anyone can see enabled taxonomies, but learners cannot see disabled taxonomies"""
        taxonomy = getattr(self, taxonomy_attr)
        taxonomy.enabled = enabled
        perm = "oel_tagging.view_taxonomy"
        self._expected_users_have_perm(perm, taxonomy, learner_obj=enabled)

    @ddt.data(
        (True, "taxonomy_no_orgs"),
        (False, "taxonomy_no_orgs"),
    )
    @ddt.unpack
    def test_view_taxonomy_no_orgs(self, enabled, taxonomy_attr):
        """
        Enabled taxonomies with no org can be viewed by anyone.
        Disabled taxonomies with no org can only be viewed by staff/superusers.
        """
        taxonomy = getattr(self, taxonomy_attr)
        taxonomy.enabled = enabled
        perm = "oel_tagging.view_taxonomy"
        assert self.superuser.has_perm(perm, taxonomy)
        assert self.staff.has_perm(perm, taxonomy)
        assert self.user_all_orgs.has_perm(perm, taxonomy) == enabled
        assert self.user_both_orgs.has_perm(perm, taxonomy) == enabled
        assert self.user_org2.has_perm(perm, taxonomy) == enabled
        assert self.learner.has_perm(perm, taxonomy) == enabled

    @ddt.data(
        ("oel_tagging.change_taxonomy", "taxonomy_no_orgs"),
        ("oel_tagging.delete_taxonomy", "taxonomy_no_orgs"),
    )
    @ddt.unpack
    def test_change_taxonomy_no_orgs(self, perm, taxonomy_attr):
        """
        Taxonomies with no org can only be changed by staff and superusers.
        """
        taxonomy = getattr(self, taxonomy_attr)
        assert self.superuser.has_perm(perm, taxonomy)
        assert self.staff.has_perm(perm, taxonomy)
        assert not self.user_all_orgs.has_perm(perm, taxonomy)
        assert not self.user_both_orgs.has_perm(perm, taxonomy)
        assert not self.user_org2.has_perm(perm, taxonomy)
        assert not self.learner.has_perm(perm, taxonomy)

    # Tag

    @ddt.data(
        ("oel_tagging.add_tag", "tag_all_orgs"),
        ("oel_tagging.add_tag", "tag_both_orgs"),
        ("oel_tagging.add_tag", "tag_disabled"),
        ("oel_tagging.change_tag", "tag_all_orgs"),
        ("oel_tagging.change_tag", "tag_both_orgs"),
        ("oel_tagging.change_tag", "tag_disabled"),
        ("oel_tagging.delete_tag", "tag_all_orgs"),
        ("oel_tagging.delete_tag", "tag_both_orgs"),
        ("oel_tagging.delete_tag", "tag_disabled"),
    )
    @ddt.unpack
    def test_change_tag_all_orgs(self, perm, tag_attr):
        """Taxonomy administrators can modify tags on non-free-text taxonomies"""
        tag = getattr(self, tag_attr)
        self._expected_users_have_perm(perm, tag)

    @ddt.data(
        ("oel_tagging.add_tag", "tag_one_org"),
        ("oel_tagging.change_tag", "tag_one_org"),
        ("oel_tagging.delete_tag", "tag_one_org"),
    )
    @ddt.unpack
    def test_change_tag_org1(self, perm, tag_attr):
        """Taxonomy administrators can modify tags on non-free-text taxonomies"""
        tag = getattr(self, tag_attr)
        self._expected_users_have_perm(perm, tag, user_org2=False)

    @ddt.data(
        "oel_tagging.add_tag",
        "oel_tagging.change_tag",
        "oel_tagging.delete_tag",
    )
    def test_tag_no_taxonomy(self, perm):
        """Taxonomy administrators can modify any Tag, even those with no Taxonnmy."""
        tag = Tag()

        # Global Taxonomy Admins can do pretty much anything
        assert self.superuser.has_perm(perm, tag)
        assert self.staff.has_perm(perm, tag)
        assert self.user_all_orgs.has_perm(perm, tag)

        # Org content creators are bound by a taxonomy's org restrictions,
        # so if there's no taxonomy, they can't do anything to it.
        assert not self.user_both_orgs.has_perm(perm, tag)
        assert not self.user_org2.has_perm(perm, tag)
        assert not self.learner.has_perm(perm, tag)

    @ddt.data(
        "tag_all_orgs",
        "tag_both_orgs",
        "tag_one_org",
        "tag_disabled",
        "tag_no_orgs",
    )
    def test_view_tag(self, tag_attr):
        """Anyone can view any Tag"""
        tag = getattr(self, tag_attr)
        self._expected_users_have_perm(
            "oel_tagging.view_tag", tag, learner_perm=True, learner_obj=True
        )

    # ObjectTag

    @ddt.data(
        ("oel_tagging.add_object_tag", "disabled_course_tag"),
        ("oel_tagging.change_object_tag", "disabled_course_tag"),
        ("oel_tagging.delete_object_tag", "disabled_course_tag"),
    )
    @ddt.unpack
    def test_object_tag_disabled_taxonomy(self, perm, tag_attr):
        """Taxonomy administrators cannot create/edit an ObjectTag with a disabled Taxonomy"""
        object_tag = getattr(self, tag_attr)
        assert self.superuser.has_perm(perm, object_tag)
        assert not self.staff.has_perm(perm, object_tag)
        assert not self.user_all_orgs.has_perm(perm, object_tag)
        assert not self.user_both_orgs.has_perm(perm, object_tag)
        assert not self.user_org2.has_perm(perm, object_tag)
        assert not self.learner.has_perm(perm, object_tag)

    @ddt.data(
        ("oel_tagging.add_object_tag", "no_orgs_invalid_tag"),
        ("oel_tagging.change_object_tag", "no_orgs_invalid_tag"),
        ("oel_tagging.delete_object_tag", "no_orgs_invalid_tag"),
    )
    @ddt.unpack
    def test_object_tag_no_orgs(self, perm, tag_attr):
        """Only staff & superusers can create/edit an ObjectTag with a no-org Taxonomy"""
        object_tag = getattr(self, tag_attr)
        assert self.superuser.has_perm(perm, object_tag)
        assert self.staff.has_perm(perm, object_tag)
        assert not self.user_all_orgs.has_perm(perm, object_tag)
        assert not self.user_both_orgs.has_perm(perm, object_tag)
        assert not self.user_org2.has_perm(perm, object_tag)
        assert not self.learner.has_perm(perm, object_tag)

    @ddt.data(
        ("oel_tagging.add_object_tag", "all_orgs_course_tag"),
        ("oel_tagging.add_object_tag", "all_orgs_block_tag"),
        ("oel_tagging.add_object_tag", "both_orgs_course_tag"),
        ("oel_tagging.add_object_tag", "both_orgs_block_tag"),
        ("oel_tagging.add_object_tag", "all_orgs_invalid_tag"),
        ("oel_tagging.change_object_tag", "all_orgs_course_tag"),
        ("oel_tagging.change_object_tag", "all_orgs_block_tag"),
        ("oel_tagging.change_object_tag", "both_orgs_course_tag"),
        ("oel_tagging.change_object_tag", "both_orgs_block_tag"),
        ("oel_tagging.change_object_tag", "all_orgs_invalid_tag"),
        ("oel_tagging.delete_object_tag", "all_orgs_course_tag"),
        ("oel_tagging.delete_object_tag", "all_orgs_block_tag"),
        ("oel_tagging.delete_object_tag", "both_orgs_course_tag"),
        ("oel_tagging.delete_object_tag", "both_orgs_block_tag"),
        ("oel_tagging.delete_object_tag", "all_orgs_invalid_tag"),
    )
    @ddt.unpack
    def test_change_object_tag_all_orgs(self, perm, tag_attr):
        """Taxonomy administrators can create/edit an ObjectTag on taxonomies in their org."""
        object_tag = getattr(self, tag_attr)
        self._expected_users_have_perm(perm, object_tag)

    @ddt.data(
        ("oel_tagging.add_object_tag", "one_org_block_tag"),
        ("oel_tagging.add_object_tag", "one_org_invalid_org_tag"),
        ("oel_tagging.change_object_tag", "one_org_block_tag"),
        ("oel_tagging.change_object_tag", "one_org_invalid_org_tag"),
        ("oel_tagging.delete_object_tag", "one_org_block_tag"),
        ("oel_tagging.delete_object_tag", "one_org_invalid_org_tag"),
    )
    @ddt.unpack
    def test_change_object_tag_org1(self, perm, tag_attr):
        """Taxonomy administrators can create/edit an ObjectTag on taxonomies in their org."""
        object_tag = getattr(self, tag_attr)
        self._expected_users_have_perm(perm, object_tag, user_org2=False)

    @ddt.data(
        "oel_tagging.add_object_tag",
        "oel_tagging.change_object_tag",
        "oel_tagging.delete_object_tag",
    )
    def test_object_tag_no_taxonomy(self, perm):
        """Taxonomy administrators can modify an ObjectTag with no Taxonomy"""
        object_tag = ObjectTag()

        # Global Taxonomy Admins can do pretty much anything
        assert self.superuser.has_perm(perm, object_tag)
        assert self.staff.has_perm(perm, object_tag)
        assert self.user_all_orgs.has_perm(perm, object_tag)

        # Org content creators are bound by a taxonomy's org restrictions,
        # so if there's no taxonomy, they can't do anything to it.
        assert not self.user_both_orgs.has_perm(perm, object_tag)
        assert not self.user_org2.has_perm(perm, object_tag)
        assert not self.learner.has_perm(perm, object_tag)

    @ddt.data(
        "all_orgs_course_tag",
        "all_orgs_block_tag",
        "both_orgs_course_tag",
        "both_orgs_block_tag",
        "one_org_block_tag",
        "all_orgs_invalid_tag",
        "one_org_invalid_org_tag",
        "no_orgs_invalid_tag",
        "disabled_course_tag",
    )
    def test_view_object_tag(self, tag_attr):
        """Anyone can view any ObjectTag"""
        object_tag = getattr(self, tag_attr)
        self._expected_users_have_perm(
            "oel_tagging.view_object_tag",
            object_tag,
            learner_perm=True,
            learner_obj=True,
        )


@ddt.ddt
@override_settings(FEATURES={"ENABLE_CREATOR_GROUP": False})
class TestRulesTaxonomyNoCreatorGroup(
    TestRulesTaxonomy
):  # pylint: disable=test-inherits-tests
    """
    Run the above tests with ENABLE_CREATOR_GROUP unset, to demonstrate that all users have course creator access for
    all orgs, and therefore everyone is a Taxonomy Administrator.

    However, if there are no Organizations in the database, then nobody has access to the Tagging models.
    """

    def _expected_users_have_perm(
        self, perm, obj, learner_perm=False, learner_obj=False, user_org2=True
    ):
        """
        When ENABLE_CREATOR_GROUP is disabled, all users have all permissions.
        """
        super()._expected_users_have_perm(
            perm=perm,
            obj=obj,
            learner_perm=True,
            learner_obj=True,
            user_org2=True,
        )

    @ddt.data(
        "oel_tagging.add_tag",
        "oel_tagging.change_tag",
        "oel_tagging.delete_tag",
    )
    def test_tag_no_taxonomy(self, perm):
        """Taxonomy administrators can modify any Tag, even those with no Taxonnmy."""
        tag = Tag()

        # Global Taxonomy Admins can do pretty much anything
        assert self.superuser.has_perm(perm, tag)
        assert self.staff.has_perm(perm, tag)
        assert self.user_all_orgs.has_perm(perm, tag)

        # Org content creators are bound by a taxonomy's org restrictions,
        # but since there's no org restrictions enabled, anyone has these permissions.
        assert self.user_both_orgs.has_perm(perm, tag)
        assert self.user_org2.has_perm(perm, tag)
        assert self.learner.has_perm(perm, tag)

    @ddt.data(
        "oel_tagging.add_object_tag",
        "oel_tagging.change_object_tag",
        "oel_tagging.delete_object_tag",
    )
    def test_object_tag_no_taxonomy(self, perm):
        """Taxonomy administrators can modify an ObjectTag with no Taxonomy"""
        object_tag = ObjectTag()

        # Global Taxonomy Admins can do pretty much anything
        assert self.superuser.has_perm(perm, object_tag)
        assert self.staff.has_perm(perm, object_tag)
        assert self.user_all_orgs.has_perm(perm, object_tag)

        # Org content creators are bound by a taxonomy's org restrictions,
        # but since there's no org restrictions enabled, anyone has these permissions.
        assert self.user_both_orgs.has_perm(perm, object_tag)
        assert self.user_org2.has_perm(perm, object_tag)
        assert self.learner.has_perm(perm, object_tag)

    # Taxonomy

    @ddt.data(
        ("oel_tagging.add_taxonomy", "taxonomy_all_orgs"),
        ("oel_tagging.add_taxonomy", "taxonomy_both_orgs"),
        ("oel_tagging.add_taxonomy", "taxonomy_disabled"),
        ("oel_tagging.add_taxonomy", "taxonomy_one_org"),
        ("oel_tagging.add_taxonomy", "taxonomy_no_orgs"),
        ("oel_tagging.change_taxonomy", "taxonomy_all_orgs"),
        ("oel_tagging.change_taxonomy", "taxonomy_both_orgs"),
        ("oel_tagging.change_taxonomy", "taxonomy_disabled"),
        ("oel_tagging.change_taxonomy", "taxonomy_one_org"),
        ("oel_tagging.change_taxonomy", "taxonomy_no_orgs"),
        ("oel_tagging.delete_taxonomy", "taxonomy_all_orgs"),
        ("oel_tagging.delete_taxonomy", "taxonomy_both_orgs"),
        ("oel_tagging.delete_taxonomy", "taxonomy_disabled"),
        ("oel_tagging.delete_taxonomy", "taxonomy_one_org"),
        ("oel_tagging.delete_taxonomy", "taxonomy_no_orgs"),
    )
    @ddt.unpack
    def test_no_orgs_no_perms(self, perm, taxonomy_attr):
        """
        Org-level permissions are revoked when there are no orgs.
        """
        Organization.objects.all().delete()
        taxonomy = getattr(self, taxonomy_attr)
        # Superusers & Staff always have access
        assert self.superuser.has_perm(perm)
        assert self.superuser.has_perm(perm, taxonomy)
        assert self.staff.has_perm(perm)
        assert self.staff.has_perm(perm, taxonomy)

        # But everyone else's object-level access is removed
        assert self.user_all_orgs.has_perm(perm)
        assert not self.user_all_orgs.has_perm(perm, taxonomy)
        assert self.user_both_orgs.has_perm(perm)
        assert not self.user_both_orgs.has_perm(perm, taxonomy)
        assert self.user_org2.has_perm(perm)
        assert not self.user_org2.has_perm(perm, taxonomy)
        assert self.learner.has_perm(perm)
        assert not self.learner.has_perm(perm, taxonomy)
