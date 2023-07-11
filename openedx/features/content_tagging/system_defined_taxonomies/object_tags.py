"""
ObjectTags for System-defined Taxonomies
"""
from openedx_tagging.core.tagging.system_defined_taxonomies.object_tags import (
    SystemDefinedIds as TaxonomyIds,
    ModelObjectTag,
    UserObjectTag,
    LanguageObjectTag,
)
from openedx_tagging.core.tagging.registry import register_object_tag_class
from organizations.models import Organization

from ..models import CourseObjectTagMixin, BlockObjectTagMixin


class SystemDefinedIds(TaxonomyIds):
    """
    System-defined taxonomy IDs
    """
    OrganizationTaxonomy = 2
    AuthorTaxonomy = 3


class OrganizationObjectTag(ModelObjectTag):
    """
    ObjectTag used on Organization system-defined taxonomy
    """

    system_defined_taxonomy_id = SystemDefinedIds.OrganizationTaxonomy.value

    class Meta:
        proxy = True

    tag_class_model = Organization


class AuthorObjcetTag(UserObjectTag):
    """
    ObjectTag used on Author system-defined taxonomy
    """

    system_defined_taxonomy_id = SystemDefinedIds.AuthorTaxonomy.value

    class Meta:
        proxy = True


class OrganizationCourseObjectTag(OrganizationObjectTag, CourseObjectTagMixin):
    """
    CourseObjectTag for use in the Organization system-defined taxonomy
    """


class OrganizationBlockObjectTag(OrganizationObjectTag, BlockObjectTagMixin):
    """
    BlockObjectTag for use in the Organization system-defined taxonomy
    """


class LanguageCourseObjectTag(LanguageObjectTag, CourseObjectTagMixin):
    """
    CourseObjectTag for use in the Language system-defined taxonomy
    """


class LanguageBlockObjectTag(LanguageObjectTag, BlockObjectTagMixin):
    """
    BlockObjectTag for use in the Language system-defined taxonomy
    """


class AuthorCourseObjectTag(AuthorObjcetTag, CourseObjectTagMixin):
    """
    CourseObjectTag for use in the Author system-defined taxonomy
    """


class AuthorBlockObjectTag(AuthorObjcetTag, BlockObjectTagMixin):
    """
    BlockObjectTag for use in the Author system-defined taxonomy
    """


# Register the object tag classes in reverse order for how we want them considered
register_object_tag_class(OrganizationCourseObjectTag)
register_object_tag_class(OrganizationBlockObjectTag)
register_object_tag_class(LanguageCourseObjectTag)
register_object_tag_class(LanguageBlockObjectTag)
register_object_tag_class(AuthorCourseObjectTag)
register_object_tag_class(AuthorBlockObjectTag)
