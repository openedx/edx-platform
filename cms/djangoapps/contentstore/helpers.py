"""
Helper methods for Studio views.
"""
from __future__ import annotations
import logging
import urllib
from lxml import etree
from mimetypes import guess_type

from attrs import frozen, Factory
from django.utils.translation import gettext as _
from opaque_keys.edx.keys import AssetKey, CourseKey, UsageKey
from opaque_keys.edx.locator import DefinitionLocator, LocalId
from xblock.core import XBlock
from xblock.fields import ScopeIds
from xblock.runtime import IdGenerator
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import contentstore
from xmodule.exceptions import NotFoundError
from xmodule.modulestore.django import modulestore
from xmodule.xml_block import XmlMixin

from cms.djangoapps.models.settings.course_grading import CourseGradingModel
import openedx.core.djangoapps.content_staging.api as content_staging_api

from .utils import reverse_course_url, reverse_library_url, reverse_usage_url

log = logging.getLogger(__name__)

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
        # The problem XBlock's display_name.default is not helpful ("Blank Problem") but changing it could have
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


@frozen
class StaticFileNotices:
    """ Information about what static files were updated (or not) when pasting content into another course """
    new_files: list[str] = Factory(list)
    conflicting_files: list[str] = Factory(list)
    error_files: list[str] = Factory(list)


def import_staged_content_from_user_clipboard(parent_key: UsageKey, request) -> tuple[XBlock | None, StaticFileNotices]:
    """
    Import a block (along with its children and any required static assets) from
    the "staged" OLX in the user's clipboard.

    Does not deal with permissions or REST stuff - do that before calling this.

    Returns (1) the newly created block on success or None if the clipboard is
    empty, and (2) a summary of changes made to static files in the destination
    course.
    """

    from cms.djangoapps.contentstore.views.preview import _load_preview_block

    if not content_staging_api:
        raise RuntimeError("The required content_staging app is not installed")
    user_clipboard = content_staging_api.get_user_clipboard(request.user.id)
    if not user_clipboard:
        # Clipboard is empty or expired/error/loading
        return None, StaticFileNotices()
    olx_str = content_staging_api.get_staged_content_olx(user_clipboard.content.id)
    static_files = content_staging_api.get_staged_content_static_files(user_clipboard.content.id)
    node = etree.fromstring(olx_str)
    store = modulestore()
    with store.bulk_operations(parent_key.course_key):
        parent_descriptor = store.get_item(parent_key)
        # Some blocks like drag-and-drop only work here with the full XBlock runtime loaded:
        parent_xblock = _load_preview_block(request, parent_descriptor)
        new_xblock = _import_xml_node_to_parent(
            node,
            parent_xblock,
            store,
            user_id=request.user.id,
            slug_hint=user_clipboard.source_usage_key.block_id,
            copied_from_block=str(user_clipboard.source_usage_key),
        )
    # Now handle static files that need to go into Files & Uploads:
    notices = _import_files_into_course(
        course_key=parent_key.context_key,
        staged_content_id=user_clipboard.content.id,
        static_files=static_files,
    )

    return new_xblock, notices


def _import_xml_node_to_parent(
    node,
    parent_xblock: XBlock,
    # The modulestore we're using
    store,
    # The ID of the user who is performing this operation
    user_id: int,
    # Hint to use as usage ID (block_id) for the new XBlock
    slug_hint: str | None = None,
    # UsageKey of the XBlock that this one is a copy of
    copied_from_block: str | None = None,
) -> XBlock:
    """
    Given an XML node representing a serialized XBlock (OLX), import it into modulestore 'store' as a child of the
    specified parent block. Recursively copy children as needed.
    """
    runtime = parent_xblock.runtime
    parent_key = parent_xblock.scope_ids.usage_id
    block_type = node.tag

    # Generate the new ID:
    id_generator = ImportIdGenerator(parent_key.context_key)
    def_id = id_generator.create_definition(block_type, slug_hint)
    usage_id = id_generator.create_usage(def_id)
    keys = ScopeIds(None, block_type, def_id, usage_id)
    # parse_xml is a really messy API. We pass both 'keys' and 'id_generator' and, depending on the XBlock, either
    # one may be used to determine the new XBlock's usage key, and the other will be ignored. e.g. video ignores
    # 'keys' and uses 'id_generator', but the default XBlock parse_xml ignores 'id_generator' and uses 'keys'.
    # For children of this block, obviously only id_generator is used.
    xblock_class = runtime.load_block_type(block_type)
    # Note: if we find a case where any XBlock needs access to the block-specific static files that were saved to
    # export_fs during copying, we could make them available here via runtime.resources_fs before calling parse_xml.
    # However, currently the only known case for that is video block's transcript files, and those will
    # automatically be "carried over" to the new XBlock even in a different course because the video ID is the same,
    # and VAL will thus make the transcript available.

    child_nodes = []
    if not xblock_class.has_children:
        # No children to worry about. The XML may contain child nodes, but they're not XBlocks.
        temp_xblock = xblock_class.parse_xml(node, runtime, keys, id_generator)
    else:
        # We have to handle the children ourselves, because there are lots of complex interactions between
        #    * the vanilla XBlock parse_xml() method, and its lack of API for "create and save a new XBlock"
        #    * the XmlMixin version of parse_xml() which only works with ImportSystem, not modulestore or the v2 runtime
        #    * the modulestore APIs for creating and saving a new XBlock, which work but don't support XML parsing.
        # We can safely assume that if the XBLock class supports children, every child node will be the XML
        # serialization of a child block, in order. For blocks that don't support children, their XML content/nodes
        # could be anything (e.g. HTML, capa)
        node_without_children = etree.Element(node.tag, **node.attrib)
        if issubclass(xblock_class, XmlMixin):
            # Hack: XBlocks that use "XmlMixin" have their own XML parsing behavior, and in particular if they encounter
            # an XML node that has no children and has only a "url_name" attribute, they'll try to load the XML data
            # from an XML file in runtime.resources_fs. But that file doesn't exist here. So we set at least one
            # additional attribute here to make sure that url_name is not the only attribute; otherwise in some cases,
            # XmlMixin.parse_xml will try to load an XML file that doesn't exist, giving an error. The name and value
            # of this attribute don't matter and should be ignored.
            node_without_children.attrib["x-is-pointer-node"] = "no"
        temp_xblock = xblock_class.parse_xml(node_without_children, runtime, keys, id_generator)
        child_nodes = list(node)
    if xblock_class.has_children and temp_xblock.children:
        raise NotImplementedError("We don't yet support pasting XBlocks with children")
    temp_xblock.parent = parent_key
    if copied_from_block:
        # Store a reference to where this block was copied from, in the 'copied_from_block' field (AuthoringMixin)
        temp_xblock.copied_from_block = copied_from_block
    # Save the XBlock into modulestore. We need to save the block and its parent for this to work:
    new_xblock = store.update_item(temp_xblock, user_id, allow_not_found=True)
    parent_xblock.children.append(new_xblock.location)
    store.update_item(parent_xblock, user_id)
    for child_node in child_nodes:
        _import_xml_node_to_parent(child_node, new_xblock, store, user_id=user_id)
    return new_xblock


def _import_files_into_course(
    course_key: CourseKey,
    staged_content_id: int,
    static_files: list[content_staging_api.StagedContentFileData],
) -> StaticFileNotices:
    """
    For the given staged static asset files (which are in "Staged Content" such as the user's clipbaord, but which
    need to end up in the course's Files & Uploads page), import them into the destination course, unless they already
    exist.
    """
    # List of files that were newly added to the destination course
    new_files = []
    # List of files that conflicted with identically named files already in the destination course
    conflicting_files = []
    # List of files that had an error (shouldn't happen unless we have some kind of bug)
    error_files = []
    for file_data_obj in static_files:
        if not isinstance(file_data_obj.source_key, AssetKey):
            # This static asset was managed by the XBlock and instead of being added to "Files & Uploads", it is stored
            # using some other system. We could make it available via runtime.resources_fs during XML parsing, but it's
            # not needed here.
            continue
        # At this point, we know this is a "Files & Uploads" asset that we may need to copy into the course:
        try:
            result = _import_file_into_course(course_key, staged_content_id, file_data_obj)
            if result is True:
                new_files.append(file_data_obj.filename)
            elif result is None:
                pass  # This file already exists; no action needed.
            else:
                conflicting_files.append(file_data_obj.filename)
        except Exception:  # lint-amnesty, pylint: disable=broad-except
            error_files.append(file_data_obj.filename)
            log.exception(f"Failed to import Files & Uploads file {file_data_obj.filename}")
    return StaticFileNotices(
        new_files=new_files,
        conflicting_files=conflicting_files,
        error_files=error_files,
    )


def _import_file_into_course(
    course_key: CourseKey,
    staged_content_id: int,
    file_data_obj: content_staging_api.StagedContentFileData,
) -> bool | None:
    """
    Import a single staged static asset file into the course, unless it already exists.
    Returns True if it was imported, False if there's a conflict, or None if
    the file already existed (no action needed).
    """
    filename = file_data_obj.filename
    new_key = course_key.make_asset_key("asset", filename)
    try:
        current_file = contentstore().find(new_key)
    except NotFoundError:
        current_file = None
    if not current_file:
        # This static asset should be imported into the new course:
        content_type = guess_type(filename)[0]
        data = content_staging_api.get_staged_content_static_file_data(staged_content_id, filename)
        if data is None:
            raise NotFoundError(file_data_obj.source_key)
        content = StaticContent(new_key, name=filename, content_type=content_type, data=data)
        # If it's an image file, also generate the thumbnail:
        thumbnail_content, thumbnail_location = contentstore().generate_thumbnail(content)
        if thumbnail_content is not None:
            content.thumbnail_location = thumbnail_location
        contentstore().save(content)
        return True
    elif current_file.content_digest == file_data_obj.md5_hash:
        # The file already exists and matches exactly, so no action is needed
        return None
    else:
        # There is a conflict with some other file that has the same name.
        return False


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
