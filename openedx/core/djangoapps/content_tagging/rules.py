"""Django rules-based permissions for tagging"""

from __future__ import annotations

from typing import Union

import django.contrib.auth.models
import openedx_tagging.core.tagging.rules as oel_tagging
import rules
from django.db.models import Q
from organizations.models import Organization

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
from .utils import get_context_key_from_key_string

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
    Returns a list of orgs (from the given list of orgs) that are associated with libraries that the given user has
    explicitly been granted read access for.

    Note: If no libraries exist for the given orgs, then no orgs will be returned, even though the user may be permitted
    to access future libraries created in these orgs.
    Nor does this mean the user may access all libraries in this org: library permissions are granted per library.
    """
    libraries = get_libraries_for_user(user, org=[org.short_name for org in orgs]).select_related('org').only('org')
    library_orgs = [library.org for library in libraries]
    return list(set(library_orgs).intersection(orgs))


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

    is_all_org, taxonomy_orgs = TaxonomyOrg.get_organizations(taxonomy)

    # Enabled all-org taxonomies can be viewed by any registred user
    if is_all_org:
        return taxonomy.enabled

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

    is_all_org, taxonomy_orgs = TaxonomyOrg.get_organizations(taxonomy)

    # Only taxonomy admins can edit all org taxonomies
    if is_all_org:
        return False

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
        return True

    try:
        context_key = get_context_key_from_key_string(object_id)
    except ValueError:
        return False

    return has_studio_write_access(user, context_key)


@rules.predicate
def can_view_object_tag_taxonomy(user: UserType, taxonomy: oel_tagging.Taxonomy) -> bool:
    """
    Only enabled taxonomy and users with permission to view this taxonomy can view object tags
    from that taxonomy.

    This rule is different from can_view_taxonomy because it checks if the taxonomy is enabled.
    """
    # Note: in the REST API, where we're dealing with multiple taxonomies at once, permissions
    # are also enforced by ObjectTagTaxonomyOrgFilterBackend.
    return not taxonomy or (taxonomy.cast().enabled and can_view_taxonomy(user, taxonomy))


@rules.predicate
def can_view_object_tag_objectid(user: UserType, object_id: str) -> bool:
    """
    Everyone that has permission to view the object should be able to tag it.
    """
    if not object_id:
        raise ValueError("object_id must be provided")

    try:
        context_key = get_context_key_from_key_string(object_id)
    except ValueError:
        return False

    return has_studio_read_access(user, context_key)


@rules.predicate
def can_change_object_tag(
    user: UserType, perm_obj: oel_tagging.ObjectTagPermissionItem | None = None
) -> bool:
    """
    Checks if the user has permissions to create or modify tags on the given taxonomy and object_id.
    """
    if not oel_tagging.can_change_object_tag(user, perm_obj):
        return False

    # The following code allows METHOD permission (PUT) in the viewset for everyone
    if perm_obj is None:
        return True

    # TaxonomySerializer use this rule passing object_id = "" to check if the user
    # can use the taxonomy
    if perm_obj.object_id == "":
        return True

    # Also skip taxonomy check if the taxonomy is not set
    if not perm_obj.taxonomy:
        return True

    # Taxonomy admins can tag any object using any taxonomy
    if oel_tagging.is_taxonomy_admin(user):
        return True

    context_key = get_context_key_from_key_string(perm_obj.object_id)

    org_short_name = context_key.org
    return perm_obj.taxonomy.taxonomyorg_set.filter(Q(org__short_name=org_short_name) | Q(org=None)).exists()


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
        or (bool(taxonomy) and not taxonomy.allow_free_text and not taxonomy.system_defined)
    )


# Taxonomy
rules.set_perm("oel_tagging.add_taxonomy", can_create_taxonomy)
rules.set_perm("oel_tagging.change_taxonomy", can_change_taxonomy)
rules.set_perm("oel_tagging.delete_taxonomy", can_change_taxonomy)
rules.set_perm("oel_tagging.view_taxonomy", can_view_taxonomy)
rules.add_perm("oel_tagging.update_orgs", oel_tagging.is_taxonomy_admin)

# Tag
rules.set_perm("oel_tagging.add_tag", can_change_taxonomy_tag)
rules.set_perm("oel_tagging.change_tag", can_change_taxonomy_tag)
rules.set_perm("oel_tagging.delete_tag", can_change_taxonomy_tag)
rules.set_perm("oel_tagging.view_tag", rules.always_allow)

# ObjectTag
rules.set_perm("oel_tagging.add_objecttag", can_change_object_tag)
rules.set_perm("oel_tagging.change_objecttag", can_change_object_tag)
rules.set_perm("oel_tagging.delete_objecttag", can_change_object_tag)
rules.set_perm("oel_tagging.view_objecttag", oel_tagging.can_view_object_tag)
rules.set_perm("oel_tagging.can_tag_object", can_change_object_tag)

# This perms are used in the tagging rest api from openedx_tagging that is exposed in the CMS. They are overridden here
# to include Organization and objects permissions.
rules.set_perm("oel_tagging.view_objecttag_taxonomy", can_view_object_tag_taxonomy)
rules.set_perm("oel_tagging.view_objecttag_objectid", can_view_object_tag_objectid)
rules.set_perm("oel_tagging.change_objecttag_taxonomy", can_view_object_tag_taxonomy)
rules.set_perm("oel_tagging.change_objecttag_objectid", can_change_object_tag_objectid)
