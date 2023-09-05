"""Django rules-based permissions for tagging"""

from __future__ import annotations

from typing import Union

import django.contrib.auth.models
import openedx_tagging.core.tagging.rules as oel_tagging
import rules

from common.djangoapps.student.auth import is_content_creator, has_studio_write_access

from .models import TaxonomyOrg

UserType = Union[django.contrib.auth.models.User, django.contrib.auth.models.AnonymousUser]


def is_taxonomy_user(user: UserType, taxonomy: oel_tagging.Taxonomy | None = None) -> bool:
    """
    Returns True if the given user is a Taxonomy User for the given content taxonomy.

    Taxonomy users include global staff and superusers, plus course creators who can create courses for any org.
    Otherwise, we need a taxonomy provided to determine if the user is an org-level course creator for one of the
    orgs allowed to use this taxonomy.
    """
    if oel_tagging.is_taxonomy_admin(user):
        return True

    if not taxonomy:
        return is_content_creator(user, None)

    taxonomy_orgs = TaxonomyOrg.get_organizations(
        taxonomy=taxonomy,
        rel_type=TaxonomyOrg.RelType.OWNER,
    )
    for org in taxonomy_orgs:
        if is_content_creator(user, org.short_name):
            return True
    return False


@rules.predicate
def can_change_object_tag_objectid(user: UserType, object_id: str) -> bool:
    """
    Everyone that has permission to edit the object should be able to tag it.
    """

    return has_studio_write_access(user, object_id)


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
rules.set_perm("oel_tagging.add_taxonomy", oel_tagging.is_taxonomy_admin)
rules.set_perm("oel_tagging.change_taxonomy", oel_tagging.can_change_taxonomy)
rules.set_perm("oel_tagging.delete_taxonomy", oel_tagging.can_change_taxonomy)
rules.set_perm("oel_tagging.view_taxonomy", oel_tagging.can_view_taxonomy)

# Tag
rules.set_perm("oel_tagging.add_tag", can_change_taxonomy_tag)
rules.set_perm("oel_tagging.change_tag", can_change_taxonomy_tag)
rules.set_perm("oel_tagging.delete_tag", can_change_taxonomy_tag)
rules.set_perm("oel_tagging.view_tag", rules.always_allow)

# ObjectTag
rules.set_perm("oel_tagging.add_object_tag", oel_tagging.can_change_object_tag)
rules.set_perm("oel_tagging.change_object_tag", oel_tagging.can_change_object_tag)
rules.set_perm("oel_tagging.delete_object_tag", oel_tagging.can_change_object_tag)
rules.set_perm("oel_tagging.view_object_tag", rules.always_allow)

# Users can tag objects using tags from any taxonomy that they have permission to view
rules.set_perm("oel_tagging.change_objecttag_taxonomy", is_taxonomy_user)
rules.set_perm("oel_tagging.change_objecttag_objectid", can_change_object_tag_objectid)
