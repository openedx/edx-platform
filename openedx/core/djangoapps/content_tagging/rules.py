"""Django rules-based permissions for tagging"""

from __future__ import annotations

from typing import Union

import django.contrib.auth.models
import openedx_tagging.core.tagging.rules as oel_tagging
from organizations.models import Organization
import rules
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey

from common.djangoapps.student.auth import has_studio_read_access, has_studio_write_access
from common.djangoapps.student.models import CourseAccessRole
from common.djangoapps.student.roles import (
    CourseInstructorRole,
    CourseStaffRole,
    OrgContentCreatorRole,
    OrgInstructorRole,
    OrgLibraryUserRole,
    OrgStaffRole
)
from openedx.core.djangoapps.content_libraries.api import get_libraries_for_user

from .models import TaxonomyOrg

UserType = Union[django.contrib.auth.models.User, django.contrib.auth.models.AnonymousUser]


def is_org_admin(user: UserType, orgs: list[Organization] | None = None) -> bool:
    """
    Return True if the given user is an admin for any of the given orgs.
    """

    return len(get_admin_orgs(user, orgs)) > 0


def is_org_user(user: UserType, orgs: list[Organization]) -> bool:
    """
    Return True if the given user is a member of any of the given orgs.
    """
    return len(get_user_orgs(user, orgs)) > 0


def get_admin_orgs(user: UserType, orgs: list[Organization] | None = None) -> list[Organization]:
    """
    Returns a list of orgs that the given user is an admin, from the given list of orgs.

    If no orgs are provided, check all orgs
    """
    org_list = Organization.objects.all() if orgs is None else orgs
    return [
        org for org in org_list if OrgStaffRole(org=org.short_name).has_user(user)
    ]


def get_content_creator_orgs(user: UserType, orgs: list[Organization]) -> list[Organization]:
    """
    Returns a list of orgs that the given user is a content creator, the given list of orgs.
    """
    return [
        org for org in orgs if (
            OrgLibraryUserRole(org=org.short_name).has_user(user) or
            OrgInstructorRole(org=org.short_name).has_user(user) or
            OrgContentCreatorRole(org=org.short_name).has_user(user)
        )
    ]


def get_instructor_orgs(user: UserType, orgs: list[Organization]) -> list[Organization]:
    """
    Returns a list of orgs that the given user is an instructor, from the given list of orgs.
    """
    instructor_roles = CourseAccessRole.objects.filter(
        org__in=(org.short_name for org in orgs),
        user=user,
        role__in=(CourseStaffRole.ROLE, CourseInstructorRole.ROLE),
    )
    instructor_orgs = [role.org for role in instructor_roles]
    return [org for org in orgs if org.short_name in instructor_orgs]


def get_library_user_orgs(user: UserType, orgs: list[Organization]) -> list[Organization]:
    """
    Returns a list of orgs that the given user has explicity permission, from the given list of orgs.
    """
    return [
        org for org in orgs if (
            len(get_libraries_for_user(user, org=org.short_name)) > 0
        )
    ]


def get_user_orgs(user: UserType, orgs: list[Organization]) -> list[Organization]:
    """
    Return a list of orgs that the given user is a member of (instructor or content creator),
    from the given list of orgs.
    """
    content_creator_orgs = get_content_creator_orgs(user, orgs)
    instructor_orgs = get_instructor_orgs(user, orgs)
    library_user_orgs = get_library_user_orgs(user, orgs)
    user_orgs = list(set(content_creator_orgs) | set(instructor_orgs) | set(library_user_orgs))

    return user_orgs


def can_create_taxonomy(user: UserType) -> bool:
    """
    Returns True if the given user can create a taxonomy.

    Taxonomy admins and org-level staff can create taxonomies.
    """
    # Taxonomy admins can view any taxonomy
    if oel_tagging.is_taxonomy_admin(user):
        return True

    # Org-level staff can create taxonomies associated with one of their orgs.
    if is_org_admin(user):
        return True

    return False


@rules.predicate
def can_view_taxonomy(user: UserType, taxonomy: oel_tagging.Taxonomy) -> bool:
    """
    Returns True if the given user can view the given taxonomy.

    Taxonomy admins can view any taxonomy.
    Org-level staff can view any taxonomy that is associated with one of their orgs.
    Org-level course creators and instructors can view any enabled taxonomy that is owned by one of their orgs.
    """
    # The following code allows METHOD permission (GET) in the viewset for everyone
    if not taxonomy:
        return True

    taxonomy = taxonomy.cast()

    # Taxonomy admins can view any taxonomy
    if oel_tagging.is_taxonomy_admin(user):
        return True

    is_all_org = TaxonomyOrg.objects.filter(
        taxonomy=taxonomy,
        org=None,
        rel_type=TaxonomyOrg.RelType.OWNER,
    ).exists()

    # Enabled all-org taxonomies can be viewed by any registred user
    if is_all_org:
        return taxonomy.enabled

    taxonomy_orgs = TaxonomyOrg.get_organizations(
        taxonomy=taxonomy,
        rel_type=TaxonomyOrg.RelType.OWNER,
    )

    # Org-level staff can view any taxonomy that is associated with one of their orgs.
    if is_org_admin(user, taxonomy_orgs):
        return True

    # Org-level course creators and instructors can view any enabled taxonomy that is owned by one of their orgs.
    if is_org_user(user, taxonomy_orgs):
        return taxonomy.enabled

    return False


@rules.predicate
def can_change_taxonomy(user: UserType, taxonomy: oel_tagging.Taxonomy) -> bool:
    """
    Returns True if the given user can edit the given taxonomy.

    System definied taxonomies cannot be edited
    Taxonomy admins can edit any non system defined taxonomies
    Only taxonomy admins can edit all org taxonomies
    Org-level staff can edit any taxonomy that is associated with one of their orgs.
    """
    # The following code allows METHOD permission (PUT, PATCH) in the viewset for everyone
    if not taxonomy:
        return True

    taxonomy = taxonomy.cast()

    # System definied taxonomies cannot be edited
    if taxonomy.system_defined:
        return False

    # Taxonomy admins can edit any non system defined taxonomies
    if oel_tagging.is_taxonomy_admin(user):
        return True

    is_all_org = TaxonomyOrg.objects.filter(
        taxonomy=taxonomy,
        org=None,
        rel_type=TaxonomyOrg.RelType.OWNER,
    ).exists()

    # Only taxonomy admins can edit all org taxonomies
    if is_all_org:
        return False

    taxonomy_orgs = TaxonomyOrg.get_organizations(
        taxonomy=taxonomy,
        rel_type=TaxonomyOrg.RelType.OWNER,
    )

    # Org-level staff can edit any taxonomy that is associated with one of their orgs.
    if is_org_admin(user, taxonomy_orgs):
        return True

    return False


@rules.predicate
def can_change_object_tag_objectid(user: UserType, object_id: str) -> bool:
    """
    Everyone that has permission to edit the object should be able to tag it.
    """
    if not object_id:
        raise ValueError("object_id must be provided")
    try:
        usage_key = UsageKey.from_string(object_id)
        if not usage_key.course_key.is_course:
            raise ValueError("object_id must be from a block or a course")
        course_key = usage_key.course_key
    except InvalidKeyError:
        course_key = CourseKey.from_string(object_id)

    return has_studio_write_access(user, course_key)


@rules.predicate
def can_view_object_tag_taxonomy(user: UserType, taxonomy: oel_tagging.Taxonomy) -> bool:
    """
    Only enabled taxonomy and users with permission to view this taxonomy can view object tags
    from that taxonomy.

    This rule is different from can_view_taxonomy because it checks if the taxonomy is enabled.
    """
    return taxonomy.cast().enabled and can_view_taxonomy(user, taxonomy)


@rules.predicate
def can_view_object_tag_objectid(user: UserType, object_id: str) -> bool:
    """
    Everyone that has permission to view the object should be able to tag it.
    """
    if not object_id:
        raise ValueError("object_id must be provided")
    try:
        usage_key = UsageKey.from_string(object_id)
        if not usage_key.course_key.is_course:
            raise ValueError("object_id must be from a block or a course")
        course_key = usage_key.course_key
    except InvalidKeyError:
        course_key = CourseKey.from_string(object_id)

    return has_studio_read_access(user, course_key)


@rules.predicate
def can_change_taxonomy_tag(user: UserType, tag: oel_tagging.Tag | None = None) -> bool:
    """
    Even taxonomy admins cannot add tags to system taxonomies (their tags are system-defined), or free-text taxonomies
    (these don't have predefined tags).
    """
    taxonomy = tag.taxonomy if tag else None
    if taxonomy:
        taxonomy = taxonomy.cast()
    return oel_tagging.is_taxonomy_admin(user) and (
        not tag
        or not taxonomy
        or (taxonomy and not taxonomy.allow_free_text and not taxonomy.system_defined)
    )


# Taxonomy
rules.set_perm("oel_tagging.add_taxonomy", can_create_taxonomy)
rules.set_perm("oel_tagging.change_taxonomy", can_change_taxonomy)
rules.set_perm("oel_tagging.delete_taxonomy", can_change_taxonomy)
rules.set_perm("oel_tagging.view_taxonomy", can_view_taxonomy)
rules.set_perm("oel_tagging.export_taxonomy", can_view_taxonomy)

# Tag
rules.set_perm("oel_tagging.add_tag", can_change_taxonomy_tag)
rules.set_perm("oel_tagging.change_tag", can_change_taxonomy_tag)
rules.set_perm("oel_tagging.delete_tag", can_change_taxonomy_tag)
rules.set_perm("oel_tagging.view_tag", rules.always_allow)

# ObjectTag
rules.set_perm("oel_tagging.add_object_tag", oel_tagging.can_change_object_tag)
rules.set_perm("oel_tagging.change_objecttag", oel_tagging.can_change_object_tag)
rules.set_perm("oel_tagging.delete_objecttag", oel_tagging.can_change_object_tag)
rules.set_perm("oel_tagging.view_objecttag", oel_tagging.can_view_object_tag)

# This perms are used in the tagging rest api from openedx_tagging that is exposed in the CMS. They are overridden here
# to include Organization and objects permissions.
rules.set_perm("oel_tagging.view_objecttag_taxonomy", can_view_object_tag_taxonomy)
rules.set_perm("oel_tagging.view_objecttag_objectid", can_view_object_tag_objectid)
rules.set_perm("oel_tagging.change_objecttag_taxonomy", can_view_object_tag_taxonomy)
rules.set_perm("oel_tagging.change_objecttag_objectid", can_change_object_tag_objectid)
