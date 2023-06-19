"""
Helper methods for Studio views.
"""

import urllib
from lxml import etree

from django.utils.translation import gettext as _
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import DefinitionLocator, LocalId
from xblock.core import XBlock
from xblock.fields import ScopeIds
from xblock.runtime import IdGenerator
from xmodule.modulestore.django import modulestore

# from cms.djangoapps.contentstore.views.preview import _load_preview_block
from cms.djangoapps.models.settings.course_grading import CourseGradingModel
from common.djangoapps.student import auth
from common.djangoapps.student.roles import CourseCreatorRole, OrgContentCreatorRole

try:
    # Technically this is a django app plugin, so we should not error if it's not installed:
    import openedx.core.djangoapps.content_staging.api as content_staging_api
except ImportError:
    content_staging_api = None

from .utils import reverse_course_url, reverse_library_url, reverse_usage_url

# Note: Grader types are used throughout the platform but most usages are simply in-line
# strings.  In addition, new grader types can be defined on the fly anytime one is needed
# (because they're just strings). This dict is an attempt to constrain the sprawl in Studio.
GRADER_TYPES = {
    "HOMEWORK": "Homework",
    "LAB": "Lab",
    "ENTRANCE_EXAM": "Entrance Exam",
    "MIDTERM_EXAM": "Midterm Exam",
    "FINAL_EXAM": "Final Exam"
}


def get_parent_xblock(xblock):
    """
    Returns the xblock that is the parent of the specified xblock, or None if it has no parent.
    """
    locator = xblock.location
    parent_location = modulestore().get_parent_location(locator)

    if parent_location is None:
        return None
    return modulestore().get_item(parent_location)


def is_unit(xblock, parent_xblock=None):
    """
    Returns true if the specified xblock is a vertical that is treated as a unit.
    A unit is a vertical that is a direct child of a sequential (aka a subsection).
    """
    if xblock.category == 'vertical':
        if parent_xblock is None:
            parent_xblock = get_parent_xblock(xblock)
        parent_category = parent_xblock.category if parent_xblock else None
        return parent_category == 'sequential'
    return False


def xblock_has_own_studio_page(xblock, parent_xblock=None):
    """
    Returns true if the specified xblock has an associated Studio page. Most xblocks do
    not have their own page but are instead shown on the page of their parent. There
    are a few exceptions:
      1. Courses
      2. Verticals that are either:
        - themselves treated as units
        - a direct child of a unit
      3. XBlocks that support children
    """
    category = xblock.category

    if is_unit(xblock, parent_xblock):
        return True
    elif category == 'vertical':
        if parent_xblock is None:
            parent_xblock = get_parent_xblock(xblock)
        return is_unit(parent_xblock) if parent_xblock else False

    # All other xblocks with children have their own page
    return xblock.has_children


def xblock_studio_url(xblock, parent_xblock=None, find_parent=False):
    """
    Returns the Studio editing URL for the specified xblock.

    You can pass the parent xblock as an optimization, to avoid needing to load
    it twice, as sometimes the parent has to be checked.

    If you pass in a leaf block that doesn't have its own Studio page, this will
    normally return None, but if you use find_parent=True, this will find the
    nearest ancestor (usually the parent unit) that does have a Studio page and
    return that URL.
    """
    if not xblock_has_own_studio_page(xblock, parent_xblock):
        if find_parent:
            while xblock and not xblock_has_own_studio_page(xblock, parent_xblock):
                xblock = parent_xblock or get_parent_xblock(xblock)
                parent_xblock = None
            if not xblock:
                return None
        else:
            return None
    category = xblock.category
    if category == 'course':
        return reverse_course_url('course_handler', xblock.location.course_key)
    elif category in ('chapter', 'sequential'):
        return '{url}?show={usage_key}'.format(
            url=reverse_course_url('course_handler', xblock.location.course_key),
            usage_key=urllib.parse.quote(str(xblock.location))
        )
    elif category == 'library':
        library_key = xblock.location.course_key
        return reverse_library_url('library_handler', library_key)
    else:
        return reverse_usage_url('container_handler', xblock.location)


def xblock_type_display_name(xblock, default_display_name=None):
    """
    Returns the display name for the specified type of xblock. Note that an instance can be passed in
    for context dependent names, e.g. a vertical beneath a sequential is a Unit.

    :param xblock: An xblock instance or the type of xblock (as a string).
    :param default_display_name: The default value to return if no display name can be found.
    :return:
    """

    if hasattr(xblock, 'category'):
        category = xblock.category
        if category == 'vertical' and not is_unit(xblock):
            return _('Vertical')
    else:
        category = xblock
    if category == 'chapter':
        return _('Section')
    elif category == 'sequential':
        return _('Subsection')
    elif category == 'vertical':
        return _('Unit')
    elif category == 'problem':
        # The problem XBlock's display_name.default is not helpful ("Blank Advanced Problem") but changing it could have
        # too many ripple effects in other places, so we have a special case for capa problems here.
        # Note: With a ProblemBlock instance, we could actually check block.problem_types to give a more specific
        # description like "Multiple Choice Problem", but that won't work if our 'block' argument is just the block_type
        # string ("problem").
        return _('Problem')
    component_class = XBlock.load_class(category)
    if hasattr(component_class, 'display_name') and component_class.display_name.default:
        return _(component_class.display_name.default)  # lint-amnesty, pylint: disable=translation-of-non-string
    else:
        return default_display_name


def xblock_primary_child_category(xblock):
    """
    Returns the primary child category for the specified xblock, or None if there is not a primary category.
    """
    category = xblock.category
    if category == 'course':
        return 'chapter'
    elif category == 'chapter':
        return 'sequential'
    elif category == 'sequential':
        return 'vertical'
    return None


def remove_entrance_exam_graders(course_key, user):
    """
    Removes existing entrance exam graders attached to the specified course
    Typically used when adding/removing an entrance exam.
    """
    grading_model = CourseGradingModel.fetch(course_key)
    graders = grading_model.graders
    for i, grader in enumerate(graders):
        if grader['type'] == GRADER_TYPES['ENTRANCE_EXAM']:
            CourseGradingModel.delete_grader(course_key, i, user)


class ImportIdGenerator(IdGenerator):
    """
    Modulestore's IdGenerator doesn't work for importing single blocks as OLX,
    so we implement our own
    """

    def __init__(self, context_key):
        super().__init__()
        self.context_key = context_key

    def create_aside(self, definition_id, usage_id, aside_type):
        """ Generate a new aside key """
        raise NotImplementedError()

    def create_usage(self, def_id) -> UsageKey:
        """ Generate a new UsageKey for an XBlock """
        # Note: Split modulestore will detect this temporary ID and create a new block ID when the XBlock is saved.
        return self.context_key.make_usage_key(def_id.block_type, LocalId())

    def create_definition(self, block_type, slug=None) -> DefinitionLocator:
        """ Generate a new definition_id for an XBlock """
        # Note: Split modulestore will detect this temporary ID and create a new definition ID when the XBlock is saved.
        return DefinitionLocator(block_type, LocalId(block_type))


def import_staged_content_from_user_clipboard(parent_key: UsageKey, request):
    """
    Import a block (and any children it has) from "staged" OLX.
    Does not deal with permissions or REST stuff - do that before calling this.

    Returns the newly created block on success or None if the clipboard is
    empty.
    """

    from cms.djangoapps.contentstore.views.preview import _load_preview_block

    if not content_staging_api:
        raise RuntimeError("The required content_staging app is not installed")
    user_clipboard = content_staging_api.get_user_clipboard(request.user.id)
    if not user_clipboard:
        # Clipboard is empty or expired/error/loading
        return None
    block_type = user_clipboard.content.block_type
    olx_str = content_staging_api.get_staged_content_olx(user_clipboard.content.id)
    node = etree.fromstring(olx_str)
    store = modulestore()
    with store.bulk_operations(parent_key.course_key):
        parent_descriptor = store.get_item(parent_key)
        # Some blocks like drag-and-drop only work here with the full XBlock runtime loaded:

        parent_xblock = _load_preview_block(request, parent_descriptor)
        runtime = parent_xblock.runtime
        # Generate the new ID:
        id_generator = ImportIdGenerator(parent_key.context_key)
        def_id = id_generator.create_definition(block_type, user_clipboard.source_usage_key.block_id)
        usage_id = id_generator.create_usage(def_id)
        keys = ScopeIds(None, block_type, def_id, usage_id)
        # parse_xml is a really messy API. We pass both 'keys' and 'id_generator' and, depending on the XBlock, either
        # one may be used to determine the new XBlock's usage key, and the other will be ignored. e.g. video ignores
        # 'keys' and uses 'id_generator', but the default XBlock parse_xml ignores 'id_generator' and uses 'keys'.
        # For children of this block, obviously only id_generator is used.
        xblock_class = runtime.load_block_type(block_type)
        temp_xblock = xblock_class.parse_xml(node, runtime, keys, id_generator)
        if xblock_class.has_children and temp_xblock.children:
            raise NotImplementedError("We don't yet support pasting XBlocks with children")
        temp_xblock.parent = parent_key
        # Store a reference to where this block was copied from, in the 'copied_from_block' field (AuthoringMixin)
        temp_xblock.copied_from_block = str(user_clipboard.source_usage_key)
        # Save the XBlock into modulestore. We need to save the block and its parent for this to work:
        new_xblock = store.update_item(temp_xblock, request.user.id, allow_not_found=True)
        parent_xblock.children.append(new_xblock.location)
        store.update_item(parent_xblock, request.user.id)
        return new_xblock


def is_item_in_course_tree(item):
    """
    Check that the item is in the course tree.

    It's possible that the item is not in the course tree
    if its parent has been deleted and is now an orphan.
    """
    ancestor = item.get_parent()
    while ancestor is not None and ancestor.location.block_type != "course":
        ancestor = ancestor.get_parent()

    return ancestor is not None


def is_content_creator(user, org):
    """
    Check if the user has the role to create content.

    This function checks if the User has role to create content
    or if the org is supplied, it checks for Org level course content
    creator.
    """
    return (auth.user_has_role(user, CourseCreatorRole()) or
            auth.user_has_role(user, OrgContentCreatorRole(org=org)))
