"""Tests content_tagging rules-based permissions"""

import ddt
from django.contrib.auth import get_user_model
from django.test.testcases import TestCase, override_settings
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from openedx_tagging.core.tagging.models import (
    Tag,
    UserSystemDefinedTaxonomy,
)
from openedx_tagging.core.tagging.rules import ChangeObjectTagPermissionItem
from organizations.models import Organization

from common.djangoapps.student.auth import add_users, update_org_role
from common.djangoapps.student.roles import CourseCreatorRole, CourseStaffRole, OrgContentCreatorRole

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

        self.course1 = CourseLocator(self.org1.short_name, "DemoX", "Demo_Course")
        self.course2 = CourseLocator(self.org2.short_name, "DemoX", "Demo_Course")
        self.courseC = CourseLocator("orgC", "DemoX", "Demo_Course")

        self.xblock1 = BlockUsageLocator(
            course_key=self.course1,
            block_type='problem',
            block_id='block_id'
        )
        self.xblock2 = BlockUsageLocator(
            course_key=self.course2,
            block_type='problem',
            block_id='block_id'
        )
        self.xblockC = BlockUsageLocator(
            course_key=self.courseC,
            block_type='problem',
            block_id='block_id'
        )

        add_users(self.staff, CourseStaffRole(self.course1), self.user_all_orgs)
        add_users(self.staff, CourseStaffRole(self.course1), self.user_both_orgs)
        add_users(self.staff, CourseStaffRole(self.course2), self.user_all_orgs)
        add_users(self.staff, CourseStaffRole(self.course2), self.user_both_orgs)
        add_users(self.staff, CourseStaffRole(self.course2), self.user_org2)
        add_users(self.staff, CourseStaffRole(self.course2), self.user_org2)

        self.tax_all_course1 = ChangeObjectTagPermissionItem(
            taxonomy=self.taxonomy_all_orgs,
            object_id=str(self.course1),
        )
        self.tax_all_course2 = ChangeObjectTagPermissionItem(
            taxonomy=self.taxonomy_all_orgs,
            object_id=str(self.course2),
        )
        self.tax_all_xblock1 = ChangeObjectTagPermissionItem(
            taxonomy=self.taxonomy_all_orgs,
            object_id=str(self.xblock1),
        )
        self.tax_all_xblock2 = ChangeObjectTagPermissionItem(
            taxonomy=self.taxonomy_all_orgs,
            object_id=str(self.xblock2),
        )

        self.tax_both_course1 = ChangeObjectTagPermissionItem(
            taxonomy=self.taxonomy_both_orgs,
            object_id=str(self.course1),
        )
        self.tax_both_course2 = ChangeObjectTagPermissionItem(
            taxonomy=self.taxonomy_both_orgs,
            object_id=str(self.course2),
        )
        self.tax_both_xblock1 = ChangeObjectTagPermissionItem(
            taxonomy=self.taxonomy_both_orgs,
            object_id=str(self.xblock1),
        )
        self.tax_both_xblock2 = ChangeObjectTagPermissionItem(
            taxonomy=self.taxonomy_both_orgs,
            object_id=str(self.xblock2),
        )

        self.tax1_course1 = ChangeObjectTagPermissionItem(
            taxonomy=self.taxonomy_one_org,
            object_id=str(self.course1),
        )
        self.tax1_xblock1 = ChangeObjectTagPermissionItem(
            taxonomy=self.taxonomy_one_org,
            object_id=str(self.xblock1),
        )

        self.tax_no_org_course1 = ChangeObjectTagPermissionItem(
            taxonomy=self.taxonomy_no_orgs,
            object_id=str(self.course1),
        )

        self.tax_no_org_xblock1 = ChangeObjectTagPermissionItem(
            taxonomy=self.taxonomy_no_orgs,
            object_id=str(self.xblock1),
        )

        self.disabled_course_tag_perm = ChangeObjectTagPermissionItem(
            taxonomy=self.taxonomy_disabled,
            object_id=str(self.course2),
        )

        self.all_org_perms = (
            self.tax_all_course1,
            self.tax_all_course2,
            self.tax_all_xblock1,
            self.tax_all_xblock2,
            self.tax_both_course1,
            self.tax_both_course2,
            self.tax_both_xblock1,
            self.tax_both_xblock2,
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
        "oel_tagging.add_taxonomy",
        "oel_tagging.change_taxonomy",
        "oel_tagging.delete_taxonomy",
    )
    def test_taxonomy_base_edit_permissions(self, perm):
        """
        Test that only Staff & Superuser can call add/edit/delete taxonomies.
        """
        assert self.superuser.has_perm(perm)
        assert self.staff.has_perm(perm)
        assert not self.user_all_orgs.has_perm(perm)
        assert not self.user_both_orgs.has_perm(perm)
        assert not self.user_org2.has_perm(perm)
        assert not self.learner.has_perm(perm)

    @ddt.data(
        "oel_tagging.view_taxonomy",
    )
    def test_taxonomy_base_view_permissions(self, perm):
        """
        Test that everyone can call view taxonomy.
        """
        assert self.superuser.has_perm(perm)
        assert self.staff.has_perm(perm)
        assert self.user_all_orgs.has_perm(perm)
        assert self.user_both_orgs.has_perm(perm)
        assert self.user_org2.has_perm(perm)
        assert self.learner.has_perm(perm)

    @ddt.data(
        ("oel_tagging.change_taxonomy", "taxonomy_all_orgs"),
        ("oel_tagging.change_taxonomy", "taxonomy_disabled"),
        ("oel_tagging.change_taxonomy", "taxonomy_both_orgs"),
        ("oel_tagging.change_taxonomy", "taxonomy_one_org"),
        ("oel_tagging.change_taxonomy", "taxonomy_no_orgs"),
        ("oel_tagging.delete_taxonomy", "taxonomy_all_orgs"),
        ("oel_tagging.delete_taxonomy", "taxonomy_disabled"),
        ("oel_tagging.delete_taxonomy", "taxonomy_both_orgs"),
        ("oel_tagging.delete_taxonomy", "taxonomy_one_org"),
        ("oel_tagging.delete_taxonomy", "taxonomy_no_orgs"),
    )
    @ddt.unpack
    def test_change_taxonomy(self, perm, taxonomy_attr):
        """
        Test that only Staff & Superuser can edit/delete taxonomies.
        """
        taxonomy = getattr(self, taxonomy_attr)
        assert self.superuser.has_perm(perm, taxonomy)
        assert self.staff.has_perm(perm, taxonomy)
        assert not self.user_all_orgs.has_perm(perm, taxonomy)
        assert not self.user_both_orgs.has_perm(perm, taxonomy)
        assert not self.user_org2.has_perm(perm, taxonomy)
        assert not self.learner.has_perm(perm, taxonomy)

    @ddt.data(
        "oel_tagging.change_taxonomy",
        "oel_tagging.delete_taxonomy",
    )
    def test_system_taxonomy(self, perm):
        """
        Test that even taxonomy administrators cannot edit/delete system taxonomies.
        """
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
        "taxonomy_all_orgs",
        "taxonomy_both_orgs",
        "taxonomy_one_org",
        "taxonomy_no_orgs",
    )
    def test_view_taxonomy_enabled(self, taxonomy_attr):
        """
        Test that anyone can view enabled taxonomies.
        """
        taxonomy = getattr(self, taxonomy_attr)
        taxonomy.enabled = True
        perm = "oel_tagging.view_taxonomy"

        assert self.superuser.has_perm(perm, taxonomy)
        assert self.staff.has_perm(perm, taxonomy)
        assert self.user_all_orgs.has_perm(perm, taxonomy)
        assert self.user_both_orgs.has_perm(perm, taxonomy)
        assert self.user_org2.has_perm(perm, taxonomy)
        assert self.learner.has_perm(perm, taxonomy)

    @ddt.data(
        "taxonomy_all_orgs",
        "taxonomy_both_orgs",
        "taxonomy_one_org",
        "taxonomy_no_orgs",
    )
    def test_view_taxonomy_disabled(self, taxonomy_attr):
        """
        Test that only Staff & Superuser can view disabled taxonomies.
        """
        taxonomy = getattr(self, taxonomy_attr)
        taxonomy.enabled = False
        perm = "oel_tagging.view_taxonomy"

        assert self.superuser.has_perm(perm, taxonomy)
        assert self.staff.has_perm(perm, taxonomy)
        assert not self.user_all_orgs.has_perm(perm, taxonomy)
        assert not self.user_both_orgs.has_perm(perm, taxonomy)
        assert not self.user_org2.has_perm(perm, taxonomy)
        assert not self.learner.has_perm(perm, taxonomy)

    # Tag

    @ddt.data(
        "oel_tagging.add_tag",
        "oel_tagging.change_tag",
        "oel_tagging.delete_tag",
    )
    def test_tag_base_edit_permissions(self, perm):
        """
        Test that only Staff & Superuser can call add/edit/delete tags.
        """
        assert self.superuser.has_perm(perm)
        assert self.staff.has_perm(perm)
        assert not self.user_all_orgs.has_perm(perm)
        assert not self.user_both_orgs.has_perm(perm)
        assert not self.user_org2.has_perm(perm)
        assert not self.learner.has_perm(perm)

    @ddt.data(
        "oel_tagging.view_tag",
    )
    def test_tag_base_view_permissions(self, perm):
        """
        Test that everyone can call view tag.
        """
        assert self.superuser.has_perm(perm)
        assert self.staff.has_perm(perm)
        assert self.user_all_orgs.has_perm(perm)
        assert self.user_both_orgs.has_perm(perm)
        assert self.user_org2.has_perm(perm)
        assert self.learner.has_perm(perm)

    @ddt.data(
        ("oel_tagging.change_tag", "tag_all_orgs"),
        ("oel_tagging.change_tag", "tag_disabled"),
        ("oel_tagging.change_tag", "tag_both_orgs"),
        ("oel_tagging.change_tag", "tag_one_org"),
        ("oel_tagging.change_tag", "tag_no_orgs"),
        ("oel_tagging.delete_tag", "tag_all_orgs"),
        ("oel_tagging.delete_tag", "tag_disabled"),
        ("oel_tagging.delete_tag", "tag_both_orgs"),
        ("oel_tagging.delete_tag", "tag_one_org"),
        ("oel_tagging.delete_tag", "tag_no_orgs"),
    )
    @ddt.unpack
    def test_change_tag(self, perm, tag_attr):
        """
        Test that only Staff & Superuser can edit/delete taxonomies.
        """
        tag = getattr(self, tag_attr)
        assert self.superuser.has_perm(perm, tag)
        assert self.staff.has_perm(perm, tag)
        assert not self.user_all_orgs.has_perm(perm, tag)
        assert not self.user_both_orgs.has_perm(perm, tag)
        assert not self.user_org2.has_perm(perm, tag)
        assert not self.learner.has_perm(perm, tag)

    @ddt.data(
        "oel_tagging.change_tag",
        "oel_tagging.delete_tag",
    )
    def test_system_taxonomy_tag(self, perm):
        """
        Test that even taxonomy administrators cannot edit/delete tags on system taxonomies.
        """
        system_taxonomy = api.create_taxonomy(
            name="System Languages",
        )
        system_taxonomy.taxonomy_class = UserSystemDefinedTaxonomy
        system_taxonomy = system_taxonomy.cast()
        tag_system_taxonomy = Tag.objects.create(
            taxonomy=system_taxonomy,
            value="en",
        )

        assert self.superuser.has_perm(perm, tag_system_taxonomy)
        assert not self.staff.has_perm(perm, tag_system_taxonomy)
        assert not self.user_all_orgs.has_perm(perm, tag_system_taxonomy)
        assert not self.user_both_orgs.has_perm(perm, tag_system_taxonomy)
        assert not self.user_org2.has_perm(perm, tag_system_taxonomy)
        assert not self.learner.has_perm(perm, tag_system_taxonomy)

    @ddt.data(
        "oel_tagging.change_tag",
        "oel_tagging.delete_tag",
    )
    def test_free_text_taxonomy_tag(self, perm):
        """
        Test that even taxonomy administrators cannot edit/delete tags on free text taxonomies.
        """
        free_text_taxonomy = api.create_taxonomy(
            name="Free text",
            allow_free_text=True,
        )

        tag_free_text_taxonomy = Tag.objects.create(
            taxonomy=free_text_taxonomy,
            value="value1",
        )

        assert self.superuser.has_perm(perm, tag_free_text_taxonomy)
        assert not self.staff.has_perm(perm, tag_free_text_taxonomy)
        assert not self.user_all_orgs.has_perm(perm, tag_free_text_taxonomy)
        assert not self.user_both_orgs.has_perm(perm, tag_free_text_taxonomy)
        assert not self.user_org2.has_perm(perm, tag_free_text_taxonomy)
        assert not self.learner.has_perm(perm, tag_free_text_taxonomy)

    @ddt.data(
        "oel_tagging.change_tag",
        "oel_tagging.delete_tag",
    )
    def test_tag_no_taxonomy(self, perm):
        """Taxonomy administrators can modify any Tag, even those with no Taxonnmy."""
        tag = Tag()

        # Global Taxonomy Admins can do pretty much anything
        assert self.superuser.has_perm(perm, tag)
        assert self.staff.has_perm(perm, tag)

        # Everyone else can't do anything
        assert not self.user_all_orgs.has_perm(perm, tag)
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
        ("oel_tagging.add_object_tag", "disabled_course_tag_perm"),
        ("oel_tagging.change_object_tag", "disabled_course_tag_perm"),
        ("oel_tagging.delete_object_tag", "disabled_course_tag_perm"),
    )
    @ddt.unpack
    def test_object_tag_disabled_taxonomy(self, perm, tag_attr):
        """Only taxonomy administrators can create/edit an ObjectTag using a disabled Taxonomy"""
        object_tag_perm = getattr(self, tag_attr)
        assert self.superuser.has_perm(perm, object_tag_perm)
        assert self.staff.has_perm(perm, object_tag_perm)
        assert not self.user_all_orgs.has_perm(perm, object_tag_perm)
        assert not self.user_both_orgs.has_perm(perm, object_tag_perm)
        assert not self.user_org2.has_perm(perm, object_tag_perm)
        assert not self.learner.has_perm(perm, object_tag_perm)

    @ddt.data(
        ("oel_tagging.add_object_tag", "tax_no_org_course1"),
        ("oel_tagging.add_object_tag", "tax_no_org_xblock1"),
        ("oel_tagging.change_object_tag", "tax_no_org_course1"),
        ("oel_tagging.change_object_tag", "tax_no_org_xblock1"),
        ("oel_tagging.delete_object_tag", "tax_no_org_xblock1"),
        ("oel_tagging.delete_object_tag", "tax_no_org_course1"),
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
        "oel_tagging.add_object_tag",
        "oel_tagging.change_object_tag",
        "oel_tagging.delete_object_tag",
    )
    def test_change_object_tag_all_orgs(self, perm):
        """
        Taxonomy administrators can create/edit an ObjectTag using taxonomies in their org,
        but only on objects they have write access to.
        """
        for perm_item in self.all_org_perms:
            assert self.superuser.has_perm(perm, perm_item)
            assert self.staff.has_perm(perm, perm_item)
            assert self.user_all_orgs.has_perm(perm, perm_item)
            assert self.user_both_orgs.has_perm(perm, perm_item)
            assert self.user_org2.has_perm(perm, perm_item) == (self.org2.short_name in perm_item.object_id)
            assert not self.learner.has_perm(perm, perm_item)

    @ddt.data(
        ("oel_tagging.add_object_tag", "tax1_course1"),
        ("oel_tagging.add_object_tag", "tax1_xblock1"),
        ("oel_tagging.change_object_tag", "tax1_course1"),
        ("oel_tagging.change_object_tag", "tax1_xblock1"),
        ("oel_tagging.delete_object_tag", "tax1_course1"),
        ("oel_tagging.delete_object_tag", "tax1_xblock1"),
    )
    @ddt.unpack
    def test_change_object_tag_org1(self, perm, tag_attr):
        """Taxonomy administrators can create/edit an ObjectTag on taxonomies in their org."""
        perm_item = getattr(self, tag_attr)
        assert self.superuser.has_perm(perm, perm_item)
        assert self.staff.has_perm(perm, perm_item)
        assert self.user_all_orgs.has_perm(perm, perm_item)
        assert self.user_both_orgs.has_perm(perm, perm_item)
        assert not self.user_org2.has_perm(perm, perm_item)
        assert not self.learner.has_perm(perm, perm_item)

    @ddt.data(
        "all_orgs_course_tag",
        "all_orgs_block_tag",
        "both_orgs_course_tag",
        "both_orgs_block_tag",
        "one_org_block_tag",
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
            learner_perm=learner_perm,
            learner_obj=learner_obj,
            user_org2=user_org2,
        )

    # Taxonomy

    @ddt.data(
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
        assert self.superuser.has_perm(perm, taxonomy)
        assert self.staff.has_perm(perm, taxonomy)

        # But everyone else's object-level access is removed
        assert not self.user_all_orgs.has_perm(perm, taxonomy)
        assert not self.user_both_orgs.has_perm(perm, taxonomy)
        assert not self.user_org2.has_perm(perm, taxonomy)
        assert not self.learner.has_perm(perm, taxonomy)
