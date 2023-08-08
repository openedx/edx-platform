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

        # No one can change or delete system taxonomy data
        self.taxonomy_system = api.create_taxonomy(
            name="System Languages",
        )
        self.taxonomy_system.taxonomy_class = UserSystemDefinedTaxonomy
        self.taxonomy_system.save()
        self.taxonomy_system = self.taxonomy_system.cast()
        self.tag_system = Tag.objects.create(
            taxonomy=self.taxonomy_system,
            value="Spanish",
        )
        self.object_tag_system = api.tag_content_object(
            taxonomy=self.taxonomy_system,
            tags=[self.tag_system.id],
            object_id=self.both_orgs_block_tag.object_id,
        )[0]

    # Taxonomy

    def test_superuser_taxonomy_perms(self):
        assert self.superuser.has_perm('oel_tagging.add_taxonomy')
        assert self.superuser.has_perm('oel_tagging.change_taxonomy')
        assert self.superuser.has_perm('oel_tagging.change_taxonomy', self.taxonomy_disabled)
        assert self.superuser.has_perm('oel_tagging.change_taxonomy', self.taxonomy_all_orgs)
        assert self.superuser.has_perm('oel_tagging.change_taxonomy', self.taxonomy_both_orgs)
        assert self.superuser.has_perm('oel_tagging.change_taxonomy', self.taxonomy_one_org)
        assert self.superuser.has_perm('oel_tagging.change_taxonomy', self.taxonomy_no_orgs)
        assert self.superuser.has_perm('oel_tagging.change_taxonomy', self.taxonomy_system)
        assert self.superuser.has_perm('oel_tagging.delete_taxonomy')
        assert self.superuser.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_disabled)
        assert self.superuser.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_all_orgs)
        assert self.superuser.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_both_orgs)
        assert self.superuser.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_one_org)
        assert self.superuser.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_no_orgs)
        assert self.superuser.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_system)

    def test_staff_taxonomy_perms(self):
        assert self.staff.has_perm('oel_tagging.add_taxonomy')
        assert self.staff.has_perm('oel_tagging.change_taxonomy')
        assert self.staff.has_perm('oel_tagging.change_taxonomy', self.taxonomy_disabled)
        assert self.staff.has_perm('oel_tagging.change_taxonomy', self.taxonomy_all_orgs)
        assert self.staff.has_perm('oel_tagging.change_taxonomy', self.taxonomy_both_orgs)
        assert self.staff.has_perm('oel_tagging.change_taxonomy', self.taxonomy_one_org)
        assert self.staff.has_perm('oel_tagging.change_taxonomy', self.taxonomy_no_orgs)
        assert not self.staff.has_perm('oel_tagging.change_taxonomy', self.taxonomy_system)
        assert self.staff.has_perm('oel_tagging.delete_taxonomy')
        assert self.staff.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_disabled)
        assert self.staff.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_all_orgs)
        assert self.staff.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_both_orgs)
        assert self.staff.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_one_org)
        assert self.staff.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_no_orgs)
        assert not self.staff.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_system)

    def test_user_all_orgs_taxonomy_perms(self):
        assert self.user_all_orgs.has_perm('oel_tagging.add_taxonomy')
        assert self.user_all_orgs.has_perm('oel_tagging.change_taxonomy')
        assert self.user_all_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_disabled)
        assert self.user_all_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_all_orgs)
        assert self.user_all_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_both_orgs)
        assert self.user_all_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_one_org)
        assert not self.user_all_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_no_orgs)
        assert not self.user_all_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_system)
        assert self.user_all_orgs.has_perm('oel_tagging.delete_taxonomy')
        assert self.user_all_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_disabled)
        assert self.user_all_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_all_orgs)
        assert self.user_all_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_both_orgs)
        assert self.user_all_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_one_org)
        assert not self.user_all_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_no_orgs)
        assert not self.user_all_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_system)

    def test_user_both_orgs_taxonomy_perms(self):
        assert not self.user_both_orgs.has_perm('oel_tagging.add_taxonomy')
        assert not self.user_both_orgs.has_perm('oel_tagging.change_taxonomy')
        assert self.user_both_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_disabled)
        assert self.user_both_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_all_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_both_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_one_org)
        assert not self.user_both_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_no_orgs)
        assert not self.user_both_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_system)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy')
        assert self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_disabled)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_all_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_both_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_one_org)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_no_orgs)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_system)

    def test_user_org2_taxonomy_perms(self):
        assert not self.user_org2.has_perm('oel_tagging.add_taxonomy')
        assert not self.user_org2.has_perm('oel_tagging.change_taxonomy')
        assert self.user_org2.has_perm('oel_tagging.change_taxonomy', self.taxonomy_disabled)
        assert self.user_org2.has_perm('oel_tagging.change_taxonomy', self.taxonomy_all_orgs)
        assert self.user_org2.has_perm('oel_tagging.change_taxonomy', self.taxonomy_both_orgs)
        assert not self.user_org2.has_perm('oel_tagging.change_taxonomy', self.taxonomy_one_org)
        assert not self.user_org2.has_perm('oel_tagging.change_taxonomy', self.taxonomy_no_orgs)
        assert not self.user_org2.has_perm('oel_tagging.change_taxonomy', self.taxonomy_system)
        assert not self.user_org2.has_perm('oel_tagging.delete_taxonomy')
        assert self.user_org2.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_disabled)
        assert self.user_org2.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_all_orgs)
        assert self.user_org2.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_both_orgs)
        assert not self.user_org2.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_one_org)
        assert not self.user_org2.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_no_orgs)
        assert not self.user_org2.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_system)

    def test_learner_taxonomy_perms(self):
        assert not self.learner.has_perm('oel_tagging.add_taxonomy')
        assert not self.learner.has_perm('oel_tagging.change_taxonomy')
        assert not self.learner.has_perm('oel_tagging.change_taxonomy', self.taxonomy_disabled)
        assert not self.learner.has_perm('oel_tagging.change_taxonomy', self.taxonomy_all_orgs)
        assert not self.learner.has_perm('oel_tagging.change_taxonomy', self.taxonomy_both_orgs)
        assert not self.learner.has_perm('oel_tagging.change_taxonomy', self.taxonomy_one_org)
        assert not self.learner.has_perm('oel_tagging.change_taxonomy', self.taxonomy_no_orgs)
        assert not self.learner.has_perm('oel_tagging.change_taxonomy', self.taxonomy_system)
        assert not self.learner.has_perm('oel_tagging.delete_taxonomy')
        assert not self.learner.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_disabled)
        assert not self.learner.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_all_orgs)
        assert not self.learner.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_both_orgs)
        assert not self.learner.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_one_org)
        assert not self.learner.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_no_orgs)
        assert not self.learner.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_system)

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

    # Tag

    def test_superuser_tag_perms(self):
        assert self.superuser.has_perm('oel_tagging.add_tag')
        assert self.superuser.has_perm('oel_tagging.change_tag')
        assert self.superuser.has_perm('oel_tagging.change_tag', self.tag_disabled)
        assert self.superuser.has_perm('oel_tagging.change_tag', self.tag_all_orgs)
        assert self.superuser.has_perm('oel_tagging.change_tag', self.tag_both_orgs)
        assert self.superuser.has_perm('oel_tagging.change_tag', self.tag_one_org)
        assert self.superuser.has_perm('oel_tagging.change_tag', self.tag_no_orgs)
        assert self.superuser.has_perm('oel_tagging.change_tag', self.tag_system)
        assert self.superuser.has_perm('oel_tagging.delete_tag')
        assert self.superuser.has_perm('oel_tagging.delete_tag', self.tag_disabled)
        assert self.superuser.has_perm('oel_tagging.delete_tag', self.tag_all_orgs)
        assert self.superuser.has_perm('oel_tagging.delete_tag', self.tag_both_orgs)
        assert self.superuser.has_perm('oel_tagging.delete_tag', self.tag_one_org)
        assert self.superuser.has_perm('oel_tagging.delete_tag', self.tag_no_orgs)
        assert self.superuser.has_perm('oel_tagging.delete_tag', self.tag_system)

    def test_staff_tag_perms(self):
        assert self.staff.has_perm('oel_tagging.add_tag')
        assert self.staff.has_perm('oel_tagging.change_tag')
        assert self.staff.has_perm('oel_tagging.change_tag', self.tag_disabled)
        assert self.staff.has_perm('oel_tagging.change_tag', self.tag_all_orgs)
        assert self.staff.has_perm('oel_tagging.change_tag', self.tag_both_orgs)
        assert self.staff.has_perm('oel_tagging.change_tag', self.tag_one_org)
        assert self.staff.has_perm('oel_tagging.change_tag', self.tag_no_orgs)
        assert not self.staff.has_perm('oel_tagging.change_tag', self.tag_system)
        assert self.staff.has_perm('oel_tagging.delete_tag')
        assert self.staff.has_perm('oel_tagging.delete_tag', self.tag_disabled)
        assert self.staff.has_perm('oel_tagging.delete_tag', self.tag_all_orgs)
        assert self.staff.has_perm('oel_tagging.delete_tag', self.tag_both_orgs)
        assert self.staff.has_perm('oel_tagging.delete_tag', self.tag_one_org)
        assert self.staff.has_perm('oel_tagging.delete_tag', self.tag_no_orgs)
        assert not self.staff.has_perm('oel_tagging.delete_tag', self.tag_system)

    def test_user_all_orgs_tag_perms(self):
        assert self.user_all_orgs.has_perm('oel_tagging.add_tag')
        assert self.user_all_orgs.has_perm('oel_tagging.change_tag')
        assert self.user_all_orgs.has_perm('oel_tagging.change_tag', self.tag_disabled)
        assert self.user_all_orgs.has_perm('oel_tagging.change_tag', self.tag_all_orgs)
        assert self.user_all_orgs.has_perm('oel_tagging.change_tag', self.tag_both_orgs)
        assert self.user_all_orgs.has_perm('oel_tagging.change_tag', self.tag_one_org)
        assert not self.user_all_orgs.has_perm('oel_tagging.change_tag', self.tag_no_orgs)
        assert not self.user_all_orgs.has_perm('oel_tagging.change_tag', self.tag_system)
        assert self.user_all_orgs.has_perm('oel_tagging.delete_tag')
        assert self.user_all_orgs.has_perm('oel_tagging.delete_tag', self.tag_disabled)
        assert self.user_all_orgs.has_perm('oel_tagging.delete_tag', self.tag_all_orgs)
        assert self.user_all_orgs.has_perm('oel_tagging.delete_tag', self.tag_both_orgs)
        assert self.user_all_orgs.has_perm('oel_tagging.delete_tag', self.tag_one_org)
        assert not self.user_all_orgs.has_perm('oel_tagging.delete_tag', self.tag_no_orgs)
        assert not self.user_all_orgs.has_perm('oel_tagging.delete_tag', self.tag_system)

    def test_user_both_orgs_tag_perms(self):
        assert not self.user_both_orgs.has_perm('oel_tagging.add_tag')
        assert not self.user_both_orgs.has_perm('oel_tagging.change_tag')
        assert self.user_both_orgs.has_perm('oel_tagging.change_tag', self.tag_disabled)
        assert self.user_both_orgs.has_perm('oel_tagging.change_tag', self.tag_all_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.change_tag', self.tag_both_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.change_tag', self.tag_one_org)
        assert not self.user_both_orgs.has_perm('oel_tagging.change_tag', self.tag_no_orgs)
        assert not self.user_both_orgs.has_perm('oel_tagging.change_tag', self.tag_system)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_tag')
        assert self.user_both_orgs.has_perm('oel_tagging.delete_tag', self.tag_disabled)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_tag', self.tag_all_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_tag', self.tag_both_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_tag', self.tag_one_org)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_tag', self.tag_no_orgs)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_tag', self.tag_system)

    def test_user_org2_tag_perms(self):
        assert not self.user_org2.has_perm('oel_tagging.add_tag')
        assert not self.user_org2.has_perm('oel_tagging.change_tag')
        assert self.user_org2.has_perm('oel_tagging.change_tag', self.tag_disabled)
        assert self.user_org2.has_perm('oel_tagging.change_tag', self.tag_all_orgs)
        assert self.user_org2.has_perm('oel_tagging.change_tag', self.tag_both_orgs)
        assert not self.user_org2.has_perm('oel_tagging.change_tag', self.tag_one_org)
        assert not self.user_org2.has_perm('oel_tagging.change_tag', self.tag_no_orgs)
        assert not self.user_org2.has_perm('oel_tagging.change_tag', self.tag_system)
        assert not self.user_org2.has_perm('oel_tagging.delete_tag')
        assert self.user_org2.has_perm('oel_tagging.delete_tag', self.tag_disabled)
        assert self.user_org2.has_perm('oel_tagging.delete_tag', self.tag_all_orgs)
        assert self.user_org2.has_perm('oel_tagging.delete_tag', self.tag_both_orgs)
        assert not self.user_org2.has_perm('oel_tagging.delete_tag', self.tag_one_org)
        assert not self.user_org2.has_perm('oel_tagging.delete_tag', self.tag_no_orgs)
        assert not self.user_org2.has_perm('oel_tagging.delete_tag', self.tag_system)

    def test_learner_tag_perms(self):
        assert not self.learner.has_perm('oel_tagging.add_tag')
        assert not self.learner.has_perm('oel_tagging.change_tag')
        assert not self.learner.has_perm('oel_tagging.change_tag', self.tag_disabled)
        assert not self.learner.has_perm('oel_tagging.change_tag', self.tag_all_orgs)
        assert not self.learner.has_perm('oel_tagging.change_tag', self.tag_both_orgs)
        assert not self.learner.has_perm('oel_tagging.change_tag', self.tag_one_org)
        assert not self.learner.has_perm('oel_tagging.change_tag', self.tag_no_orgs)
        assert not self.learner.has_perm('oel_tagging.change_tag', self.tag_system)
        assert not self.learner.has_perm('oel_tagging.delete_tag')
        assert not self.learner.has_perm('oel_tagging.delete_tag', self.tag_disabled)
        assert not self.learner.has_perm('oel_tagging.delete_tag', self.tag_all_orgs)
        assert not self.learner.has_perm('oel_tagging.delete_tag', self.tag_both_orgs)
        assert not self.learner.has_perm('oel_tagging.delete_tag', self.tag_one_org)
        assert not self.learner.has_perm('oel_tagging.delete_tag', self.tag_no_orgs)
        assert not self.learner.has_perm('oel_tagging.delete_tag', self.tag_system)

    # ObjectTag

    def test_superuser_object_tag_perms(self):
        assert self.superuser.has_perm('oel_tagging.add_object_tag')
        assert self.superuser.has_perm('oel_tagging.change_object_tag')
        assert self.superuser.has_perm('oel_tagging.change_object_tag', self.disabled_course_tag)
        assert self.superuser.has_perm('oel_tagging.change_object_tag', self.all_orgs_block_tag)
        assert self.superuser.has_perm('oel_tagging.change_object_tag', self.both_orgs_course_tag)
        assert self.superuser.has_perm('oel_tagging.change_object_tag', self.one_org_block_tag)
        assert self.superuser.has_perm('oel_tagging.change_object_tag', self.no_orgs_invalid_tag)
        assert self.superuser.has_perm('oel_tagging.change_object_tag', self.object_tag_system)
        assert self.superuser.has_perm('oel_tagging.delete_object_tag')
        assert self.superuser.has_perm('oel_tagging.delete_object_tag', self.disabled_course_tag)
        assert self.superuser.has_perm('oel_tagging.delete_object_tag', self.all_orgs_block_tag)
        assert self.superuser.has_perm('oel_tagging.delete_object_tag', self.both_orgs_course_tag)
        assert self.superuser.has_perm('oel_tagging.delete_object_tag', self.one_org_block_tag)
        assert self.superuser.has_perm('oel_tagging.delete_object_tag', self.no_orgs_invalid_tag)
        assert self.superuser.has_perm('oel_tagging.delete_object_tag', self.object_tag_system)

    def test_staff_object_tag_perms(self):
        assert self.staff.has_perm('oel_tagging.add_object_tag')
        assert self.staff.has_perm('oel_tagging.change_object_tag')
        assert not self.staff.has_perm('oel_tagging.change_object_tag', self.disabled_course_tag)
        assert self.staff.has_perm('oel_tagging.change_object_tag', self.all_orgs_block_tag)
        assert self.staff.has_perm('oel_tagging.change_object_tag', self.both_orgs_course_tag)
        assert self.staff.has_perm('oel_tagging.change_object_tag', self.one_org_block_tag)
        assert self.staff.has_perm('oel_tagging.change_object_tag', self.no_orgs_invalid_tag)
        assert self.staff.has_perm('oel_tagging.change_object_tag', self.object_tag_system)
        assert self.staff.has_perm('oel_tagging.delete_object_tag')
        assert not self.staff.has_perm('oel_tagging.delete_object_tag', self.disabled_course_tag)
        assert self.staff.has_perm('oel_tagging.delete_object_tag', self.all_orgs_block_tag)
        assert self.staff.has_perm('oel_tagging.delete_object_tag', self.both_orgs_course_tag)
        assert self.staff.has_perm('oel_tagging.delete_object_tag', self.one_org_block_tag)
        assert self.staff.has_perm('oel_tagging.delete_object_tag', self.no_orgs_invalid_tag)
        assert self.staff.has_perm('oel_tagging.delete_object_tag', self.object_tag_system)

    def test_user_all_orgs_object_tag_perms(self):
        assert self.user_all_orgs.has_perm('oel_tagging.add_object_tag')
        assert self.user_all_orgs.has_perm('oel_tagging.change_object_tag')
        assert not self.user_all_orgs.has_perm('oel_tagging.change_object_tag', self.disabled_course_tag)
        assert self.user_all_orgs.has_perm('oel_tagging.change_object_tag', self.all_orgs_block_tag)
        assert self.user_all_orgs.has_perm('oel_tagging.change_object_tag', self.both_orgs_course_tag)
        assert self.user_all_orgs.has_perm('oel_tagging.change_object_tag', self.one_org_block_tag)
        assert not self.user_all_orgs.has_perm('oel_tagging.change_object_tag', self.no_orgs_invalid_tag)
        assert not self.user_all_orgs.has_perm('oel_tagging.change_object_tag', self.object_tag_system)
        assert self.user_all_orgs.has_perm('oel_tagging.delete_object_tag')
        assert not self.user_all_orgs.has_perm('oel_tagging.delete_object_tag', self.disabled_course_tag)
        assert self.user_all_orgs.has_perm('oel_tagging.delete_object_tag', self.all_orgs_block_tag)
        assert self.user_all_orgs.has_perm('oel_tagging.delete_object_tag', self.both_orgs_course_tag)
        assert self.user_all_orgs.has_perm('oel_tagging.delete_object_tag', self.one_org_block_tag)
        assert not self.user_all_orgs.has_perm('oel_tagging.delete_object_tag', self.no_orgs_invalid_tag)
        assert not self.user_all_orgs.has_perm('oel_tagging.delete_object_tag', self.object_tag_system)

    def test_user_both_orgs_object_tag_perms(self):
        assert not self.user_both_orgs.has_perm('oel_tagging.add_object_tag')
        assert not self.user_both_orgs.has_perm('oel_tagging.change_object_tag')
        assert not self.user_both_orgs.has_perm('oel_tagging.change_object_tag', self.disabled_course_tag)
        assert self.user_both_orgs.has_perm('oel_tagging.change_object_tag', self.all_orgs_block_tag)
        assert self.user_both_orgs.has_perm('oel_tagging.change_object_tag', self.both_orgs_course_tag)
        assert self.user_both_orgs.has_perm('oel_tagging.change_object_tag', self.one_org_block_tag)
        assert not self.user_both_orgs.has_perm('oel_tagging.change_object_tag', self.no_orgs_invalid_tag)
        assert not self.user_both_orgs.has_perm('oel_tagging.change_object_tag', self.object_tag_system)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_object_tag')
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_object_tag', self.disabled_course_tag)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_object_tag', self.all_orgs_block_tag)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_object_tag', self.both_orgs_course_tag)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_object_tag', self.one_org_block_tag)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_object_tag', self.no_orgs_invalid_tag)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_object_tag', self.object_tag_system)

    def test_user_org2_object_tag_perms(self):
        assert not self.user_org2.has_perm('oel_tagging.add_object_tag')
        assert not self.user_org2.has_perm('oel_tagging.change_object_tag')
        assert not self.user_org2.has_perm('oel_tagging.change_object_tag', self.disabled_course_tag)
        assert self.user_org2.has_perm('oel_tagging.change_object_tag', self.all_orgs_block_tag)
        assert self.user_org2.has_perm('oel_tagging.change_object_tag', self.both_orgs_course_tag)
        assert not self.user_org2.has_perm('oel_tagging.change_object_tag', self.one_org_block_tag)
        assert not self.user_org2.has_perm('oel_tagging.change_object_tag', self.no_orgs_invalid_tag)
        assert not self.user_org2.has_perm('oel_tagging.change_object_tag', self.object_tag_system)
        assert not self.user_org2.has_perm('oel_tagging.delete_object_tag')
        assert not self.user_org2.has_perm('oel_tagging.delete_object_tag', self.disabled_course_tag)
        assert self.user_org2.has_perm('oel_tagging.delete_object_tag', self.all_orgs_block_tag)
        assert self.user_org2.has_perm('oel_tagging.delete_object_tag', self.both_orgs_course_tag)
        assert not self.user_org2.has_perm('oel_tagging.delete_object_tag', self.one_org_block_tag)
        assert not self.user_org2.has_perm('oel_tagging.delete_object_tag', self.no_orgs_invalid_tag)
        assert not self.user_org2.has_perm('oel_tagging.delete_object_tag', self.object_tag_system)

    def test_learner_object_tag_perms(self):
        assert not self.learner.has_perm('oel_tagging.add_object_tag')
        assert not self.learner.has_perm('oel_tagging.change_object_tag')
        assert not self.learner.has_perm('oel_tagging.change_object_tag', self.disabled_course_tag)
        assert not self.learner.has_perm('oel_tagging.change_object_tag', self.all_orgs_block_tag)
        assert not self.learner.has_perm('oel_tagging.change_object_tag', self.both_orgs_course_tag)
        assert not self.learner.has_perm('oel_tagging.change_object_tag', self.one_org_block_tag)
        assert not self.learner.has_perm('oel_tagging.change_object_tag', self.no_orgs_invalid_tag)
        assert not self.learner.has_perm('oel_tagging.change_object_tag', self.object_tag_system)
        assert not self.learner.has_perm('oel_tagging.delete_object_tag')
        assert not self.learner.has_perm('oel_tagging.delete_object_tag', self.disabled_course_tag)
        assert not self.learner.has_perm('oel_tagging.delete_object_tag', self.all_orgs_block_tag)
        assert not self.learner.has_perm('oel_tagging.delete_object_tag', self.both_orgs_course_tag)
        assert not self.learner.has_perm('oel_tagging.delete_object_tag', self.one_org_block_tag)
        assert not self.learner.has_perm('oel_tagging.delete_object_tag', self.no_orgs_invalid_tag)
        assert not self.learner.has_perm('oel_tagging.delete_object_tag', self.object_tag_system)

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

    # Taxonomy

    def test_user_both_orgs_taxonomy_perms(self):
        assert self.user_both_orgs.has_perm('oel_tagging.add_taxonomy')
        assert self.user_both_orgs.has_perm('oel_tagging.change_taxonomy')
        assert self.user_both_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_disabled)
        assert self.user_both_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_all_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_both_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_one_org)
        assert not self.user_both_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_no_orgs)
        assert not self.user_both_orgs.has_perm('oel_tagging.change_taxonomy', self.taxonomy_system)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy')
        assert self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_disabled)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_all_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_both_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_one_org)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_no_orgs)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_system)

    def test_user_org2_taxonomy_perms(self):
        assert self.user_org2.has_perm('oel_tagging.add_taxonomy')
        assert self.user_org2.has_perm('oel_tagging.change_taxonomy')
        assert self.user_org2.has_perm('oel_tagging.change_taxonomy', self.taxonomy_disabled)
        assert self.user_org2.has_perm('oel_tagging.change_taxonomy', self.taxonomy_all_orgs)
        assert self.user_org2.has_perm('oel_tagging.change_taxonomy', self.taxonomy_both_orgs)
        assert self.user_org2.has_perm('oel_tagging.change_taxonomy', self.taxonomy_one_org)
        assert not self.user_org2.has_perm('oel_tagging.change_taxonomy', self.taxonomy_no_orgs)
        assert not self.user_org2.has_perm('oel_tagging.change_taxonomy', self.taxonomy_system)
        assert self.user_org2.has_perm('oel_tagging.delete_taxonomy')
        assert self.user_org2.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_disabled)
        assert self.user_org2.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_all_orgs)
        assert self.user_org2.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_both_orgs)
        assert self.user_org2.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_one_org)
        assert not self.user_org2.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_no_orgs)
        assert not self.user_org2.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_system)

    def test_learner_taxonomy_perms(self):
        assert self.learner.has_perm('oel_tagging.add_taxonomy')
        assert self.learner.has_perm('oel_tagging.change_taxonomy')
        assert self.learner.has_perm('oel_tagging.change_taxonomy', self.taxonomy_disabled)
        assert self.learner.has_perm('oel_tagging.change_taxonomy', self.taxonomy_all_orgs)
        assert self.learner.has_perm('oel_tagging.change_taxonomy', self.taxonomy_both_orgs)
        assert self.learner.has_perm('oel_tagging.change_taxonomy', self.taxonomy_one_org)
        assert not self.learner.has_perm('oel_tagging.change_taxonomy', self.taxonomy_no_orgs)
        assert not self.learner.has_perm('oel_tagging.change_taxonomy', self.taxonomy_system)
        assert self.learner.has_perm('oel_tagging.delete_taxonomy')
        assert self.learner.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_disabled)
        assert self.learner.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_all_orgs)
        assert self.learner.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_both_orgs)
        assert self.learner.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_one_org)
        assert not self.learner.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_no_orgs)
        assert not self.learner.has_perm('oel_tagging.delete_taxonomy', self.taxonomy_system)

    # Tags

    def test_user_both_orgs_tag_perms(self):
        assert self.user_both_orgs.has_perm('oel_tagging.add_tag')
        assert self.user_both_orgs.has_perm('oel_tagging.change_tag')
        assert self.user_both_orgs.has_perm('oel_tagging.change_tag', self.tag_disabled)
        assert self.user_both_orgs.has_perm('oel_tagging.change_tag', self.tag_all_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.change_tag', self.tag_both_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.change_tag', self.tag_one_org)
        assert not self.user_both_orgs.has_perm('oel_tagging.change_tag', self.tag_no_orgs)
        assert not self.user_both_orgs.has_perm('oel_tagging.change_tag', self.tag_system)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_tag')
        assert self.user_both_orgs.has_perm('oel_tagging.delete_tag', self.tag_disabled)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_tag', self.tag_all_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_tag', self.tag_both_orgs)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_tag', self.tag_one_org)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_tag', self.tag_no_orgs)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_tag', self.tag_system)

    def test_user_org2_tag_perms(self):
        assert self.user_org2.has_perm('oel_tagging.add_tag')
        assert self.user_org2.has_perm('oel_tagging.change_tag')
        assert self.user_org2.has_perm('oel_tagging.change_tag', self.tag_disabled)
        assert self.user_org2.has_perm('oel_tagging.change_tag', self.tag_all_orgs)
        assert self.user_org2.has_perm('oel_tagging.change_tag', self.tag_both_orgs)
        assert self.user_org2.has_perm('oel_tagging.change_tag', self.tag_one_org)
        assert not self.user_org2.has_perm('oel_tagging.change_tag', self.tag_no_orgs)
        assert not self.user_org2.has_perm('oel_tagging.change_tag', self.tag_system)
        assert self.user_org2.has_perm('oel_tagging.delete_tag')
        assert self.user_org2.has_perm('oel_tagging.delete_tag', self.tag_disabled)
        assert self.user_org2.has_perm('oel_tagging.delete_tag', self.tag_all_orgs)
        assert self.user_org2.has_perm('oel_tagging.delete_tag', self.tag_both_orgs)
        assert self.user_org2.has_perm('oel_tagging.delete_tag', self.tag_one_org)
        assert not self.user_org2.has_perm('oel_tagging.delete_tag', self.tag_no_orgs)
        assert not self.user_org2.has_perm('oel_tagging.delete_tag', self.tag_system)

    def test_learner_tag_perms(self):
        assert self.learner.has_perm('oel_tagging.add_tag')
        assert self.learner.has_perm('oel_tagging.change_tag')
        assert self.learner.has_perm('oel_tagging.change_tag', self.tag_disabled)
        assert self.learner.has_perm('oel_tagging.change_tag', self.tag_all_orgs)
        assert self.learner.has_perm('oel_tagging.change_tag', self.tag_both_orgs)
        assert self.learner.has_perm('oel_tagging.change_tag', self.tag_one_org)
        assert not self.learner.has_perm('oel_tagging.change_tag', self.tag_no_orgs)
        assert not self.learner.has_perm('oel_tagging.change_tag', self.tag_system)
        assert self.learner.has_perm('oel_tagging.delete_tag')
        assert self.learner.has_perm('oel_tagging.delete_tag', self.tag_disabled)
        assert self.learner.has_perm('oel_tagging.delete_tag', self.tag_all_orgs)
        assert self.learner.has_perm('oel_tagging.delete_tag', self.tag_both_orgs)
        assert self.learner.has_perm('oel_tagging.delete_tag', self.tag_one_org)
        assert not self.learner.has_perm('oel_tagging.delete_tag', self.tag_no_orgs)
        assert not self.learner.has_perm('oel_tagging.delete_tag', self.tag_system)

    # ObjectTags

    def test_user_both_orgs_object_tag_perms(self):
        assert self.user_both_orgs.has_perm('oel_tagging.add_object_tag')
        assert self.user_both_orgs.has_perm('oel_tagging.change_object_tag')
        assert not self.user_both_orgs.has_perm('oel_tagging.change_object_tag', self.disabled_course_tag)
        assert self.user_both_orgs.has_perm('oel_tagging.change_object_tag', self.all_orgs_block_tag)
        assert self.user_both_orgs.has_perm('oel_tagging.change_object_tag', self.both_orgs_course_tag)
        assert self.user_both_orgs.has_perm('oel_tagging.change_object_tag', self.one_org_block_tag)
        assert not self.user_both_orgs.has_perm('oel_tagging.change_object_tag', self.no_orgs_invalid_tag)
        assert not self.user_both_orgs.has_perm('oel_tagging.change_object_tag', self.object_tag_system)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_object_tag')
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_object_tag', self.disabled_course_tag)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_object_tag', self.all_orgs_block_tag)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_object_tag', self.both_orgs_course_tag)
        assert self.user_both_orgs.has_perm('oel_tagging.delete_object_tag', self.one_org_block_tag)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_object_tag', self.no_orgs_invalid_tag)
        assert not self.user_both_orgs.has_perm('oel_tagging.delete_object_tag', self.object_tag_system)

    def test_user_org2_object_tag_perms(self):
        assert self.user_org2.has_perm('oel_tagging.add_object_tag')
        assert self.user_org2.has_perm('oel_tagging.change_object_tag')
        assert not self.user_org2.has_perm('oel_tagging.change_object_tag', self.disabled_course_tag)
        assert self.user_org2.has_perm('oel_tagging.change_object_tag', self.all_orgs_block_tag)
        assert self.user_org2.has_perm('oel_tagging.change_object_tag', self.both_orgs_course_tag)
        assert self.user_org2.has_perm('oel_tagging.change_object_tag', self.one_org_block_tag)
        assert not self.user_org2.has_perm('oel_tagging.change_object_tag', self.no_orgs_invalid_tag)
        assert not self.user_org2.has_perm('oel_tagging.change_object_tag', self.object_tag_system)
        assert self.user_org2.has_perm('oel_tagging.delete_object_tag')
        assert not self.user_org2.has_perm('oel_tagging.delete_object_tag', self.disabled_course_tag)
        assert self.user_org2.has_perm('oel_tagging.delete_object_tag', self.all_orgs_block_tag)
        assert self.user_org2.has_perm('oel_tagging.delete_object_tag', self.both_orgs_course_tag)
        assert self.user_org2.has_perm('oel_tagging.delete_object_tag', self.one_org_block_tag)
        assert not self.user_org2.has_perm('oel_tagging.delete_object_tag', self.no_orgs_invalid_tag)
        assert not self.user_org2.has_perm('oel_tagging.delete_object_tag', self.object_tag_system)

    def test_learner_object_tag_perms(self):
        assert self.learner.has_perm('oel_tagging.add_object_tag')
        assert self.learner.has_perm('oel_tagging.change_object_tag')
        assert not self.learner.has_perm('oel_tagging.change_object_tag', self.disabled_course_tag)
        assert self.learner.has_perm('oel_tagging.change_object_tag', self.all_orgs_block_tag)
        assert self.learner.has_perm('oel_tagging.change_object_tag', self.both_orgs_course_tag)
        assert self.learner.has_perm('oel_tagging.change_object_tag', self.one_org_block_tag)
        assert not self.learner.has_perm('oel_tagging.change_object_tag', self.no_orgs_invalid_tag)
        assert not self.learner.has_perm('oel_tagging.change_object_tag', self.object_tag_system)
        assert self.learner.has_perm('oel_tagging.delete_object_tag')
        assert not self.learner.has_perm('oel_tagging.delete_object_tag', self.disabled_course_tag)
        assert self.learner.has_perm('oel_tagging.delete_object_tag', self.all_orgs_block_tag)
        assert self.learner.has_perm('oel_tagging.delete_object_tag', self.both_orgs_course_tag)
        assert self.learner.has_perm('oel_tagging.delete_object_tag', self.one_org_block_tag)
        assert not self.learner.has_perm('oel_tagging.delete_object_tag', self.no_orgs_invalid_tag)
        assert not self.learner.has_perm('oel_tagging.delete_object_tag', self.object_tag_system)

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
