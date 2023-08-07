"""Django rules-based permissions for tagging"""

import openedx_tagging.core.tagging.rules as oel_tagging
import rules
from django.contrib.auth import get_user_model

from common.djangoapps.student.auth import is_content_creator

from .models import TaxonomyOrg

User = get_user_model()


def is_taxonomy_admin(user: User, taxonomy: oel_tagging.Taxonomy = None) -> bool:
    """
    Returns True if the given user is a Taxonomy Admin for the given content taxonomy.

    Global Taxonomy Admins include global staff and superusers, plus course creators who can create courses for any org.
    Otherwise, a taxonomy must be provided to determine if the user is a org-level course creator for one of the
    taxonomy's org owners.
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
def can_view_taxonomy(user: User, taxonomy: oel_tagging.Taxonomy = None) -> bool:
    """
    Anyone can view an enabled taxonomy,
    but only taxonomy admins can view a disabled taxonomy.
    """
    if taxonomy:
        taxonomy = taxonomy.cast()
    return (taxonomy and taxonomy.enabled) or is_taxonomy_admin(user, taxonomy)


@rules.predicate
def can_change_taxonomy(user: User, taxonomy: oel_tagging.Taxonomy = None) -> bool:
    """
    Even taxonomy admins cannot change system taxonomies.
    """
    if taxonomy:
        taxonomy = taxonomy.cast()
    return is_taxonomy_admin(user, taxonomy) and (
        not taxonomy or (taxonomy and not taxonomy.system_defined)
    )


@rules.predicate
def can_change_taxonomy_tag(user: User, tag: oel_tagging.Tag = None) -> bool:
    """
    Even taxonomy admins cannot add tags to system taxonomies (their tags are system-defined), or free-text taxonomies
    (these don't have predefined tags).
    """
    taxonomy = tag.taxonomy if tag else None
    if taxonomy:
        taxonomy = taxonomy.cast()
    return is_taxonomy_admin(user, taxonomy) and (
        not tag
        or not taxonomy
        or (taxonomy and not taxonomy.allow_free_text and not taxonomy.system_defined)
    )


@rules.predicate
def can_change_object_tag(user: User, object_tag: oel_tagging.ObjectTag = None) -> bool:
    """
    Taxonomy admins can create or modify object tags on enabled taxonomies.
    """
    taxonomy = object_tag.taxonomy if object_tag else None
    if taxonomy:
        taxonomy = taxonomy.cast()
    return is_taxonomy_admin(user, taxonomy) and (
        not object_tag or not taxonomy or (taxonomy and taxonomy.cast().enabled)
    )


# Taxonomy
rules.set_perm("oel_tagging.add_taxonomy", can_change_taxonomy)
rules.set_perm("oel_tagging.change_taxonomy", can_change_taxonomy)
rules.set_perm("oel_tagging.delete_taxonomy", can_change_taxonomy)
rules.set_perm("oel_tagging.view_taxonomy", can_view_taxonomy)

# Tag
rules.set_perm("oel_tagging.add_tag", can_change_taxonomy_tag)
rules.set_perm("oel_tagging.change_tag", can_change_taxonomy_tag)
rules.set_perm("oel_tagging.delete_tag", can_change_taxonomy_tag)
rules.set_perm("oel_tagging.view_tag", rules.always_allow)

# ObjectTag
rules.set_perm("oel_tagging.add_object_tag", can_change_object_tag)
rules.set_perm("oel_tagging.change_object_tag", can_change_object_tag)
rules.set_perm("oel_tagging.delete_object_tag", can_change_object_tag)
rules.set_perm("oel_tagging.view_object_tag", rules.always_allow)
