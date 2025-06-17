"""
Python API for interacting with edx-platform's new XBlock Runtime.

For content in modulestore (currently all course content), you'll need to use
the older runtime.

Note that these views are only for interacting with existing blocks. Other
Studio APIs cover use cases like adding/deleting/editing blocks.
"""
# pylint: disable=unused-import
from enum import Enum
from datetime import datetime
import logging
import threading

import bson.tz_util
from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.utils.translation import gettext as _
from openedx_learning.api import authoring as authoring_api
from openedx_learning.api.authoring_models import Component, ComponentVersion
from opaque_keys.edx.keys import UsageKeyV2
from opaque_keys.edx.locator import LibraryUsageLocatorV2
from rest_framework.exceptions import NotFound
from xblock.core import XBlock
from xblock.exceptions import NoSuchUsage, NoSuchViewError
from xblock.plugin import PluginMissingError

from openedx.core.types import User as UserType
from openedx.core.djangoapps.xblock.apps import get_xblock_app_config
from openedx.core.djangoapps.xblock.learning_context.manager import get_learning_context_impl
from openedx.core.djangoapps.xblock.runtime.learning_core_runtime import (
    LearningCoreFieldData,
    LearningCoreXBlockRuntime,
)
from .data import CheckPerm, LatestVersion
from .rest_api.url_converters import VersionConverter
from .utils import (
    get_secure_token_for_xblock_handler,
    get_xblock_id_for_anonymous_user,
    get_auto_latest_version,
)

from .runtime.learning_core_runtime import LearningCoreXBlockRuntime

# Made available as part of this package's public API:
from openedx.core.djangoapps.xblock.learning_context import LearningContext

# Implementation:

log = logging.getLogger(__name__)


def get_runtime(user: UserType):
    """
    Return a new XBlockRuntime.

    Each XBlockRuntime is bound to one user (and usually one request or one
    celery task). It is typically used just to load and render a single block,
    but the API _does_ allow a single runtime instance to load multiple blocks
    (as long as they're for the same user).
    """
    params = get_xblock_app_config().get_runtime_params()
    params.update(
        handler_url=get_handler_url,
        authored_data_store=LearningCoreFieldData(),
    )
    runtime = LearningCoreXBlockRuntime(user, **params)

    return runtime


def load_block(
    usage_key: UsageKeyV2,
    user: UserType,
    *,
    check_permission: CheckPerm | None = CheckPerm.CAN_LEARN,
    version: int | LatestVersion = LatestVersion.AUTO,
):
    """
    Load the specified XBlock for the given user.

    Returns an instantiated XBlock.

    Exceptions:
        NotFound - if the XBlock doesn't exist
        PermissionDenied - if the user doesn't have the necessary permissions

    Args:
        usage_key(OpaqueKey): block identifier
        user(User): user requesting the block
    """
    # Is this block part of a course, a library, or what?
    # Get the Learning Context Implementation based on the usage key
    context_impl = get_learning_context_impl(usage_key)

    # Now, check if the block exists in this context and if the user has
    # permission to render this XBlock view:
    if check_permission and user is not None:
        if check_permission == CheckPerm.CAN_EDIT:
            has_perm = context_impl.can_edit_block(user, usage_key)
        elif check_permission == CheckPerm.CAN_READ_AS_AUTHOR:
            has_perm = context_impl.can_view_block_for_editing(user, usage_key)
        elif check_permission == CheckPerm.CAN_LEARN:
            has_perm = context_impl.can_view_block(user, usage_key)
        else:
            has_perm = False
        if not has_perm:
            raise PermissionDenied(f"You don't have permission to access the component '{usage_key}'.")

    # TODO: load field overrides from the context
    # e.g. a course might specify that all 'problem' XBlocks have 'max_attempts'
    # set to 3.
    # field_overrides = context_impl.get_field_overrides(usage_key)
    runtime = get_runtime(user=user)

    try:
        return runtime.get_block(usage_key, version=version)
    except NoSuchUsage as exc:
        # Convert NoSuchUsage to NotFound so we do the right thing (404 not 500) by default.
        raise NotFound(f"The component '{usage_key}' does not exist.") from exc
    except ComponentVersion.DoesNotExist as exc:
        # Convert ComponentVersion.DoesNotExist to NotFound so we do the right thing (404 not 500) by default.
        raise NotFound(f"The requested version of component '{usage_key}' does not exist.") from exc


def get_block_metadata(block, includes=()):
    """
    Get metadata about the specified XBlock.

    This metadata is the same for all users. Any data which varies per-user must
    be served from a different API.

    Optionally provide a list or set of metadata keys to include. Valid keys are:
        index_dictionary: a dictionary of data used to add this XBlock's content
            to a search index.
        student_view_data: data needed to render the XBlock on mobile or in
            custom frontends.
        children: list of usage keys of the XBlock's children
        editable_children: children in the same bundle, as opposed to linked
            children in other bundles.
    """
    data = {
        "block_id": str(block.scope_ids.usage_id),
        "block_type": block.scope_ids.block_type,
        "display_name": get_block_display_name(block),
    }

    if "index_dictionary" in includes:
        data["index_dictionary"] = block.index_dictionary()

    if "student_view_data" in includes:
        data["student_view_data"] = block.student_view_data() if hasattr(block, 'student_view_data') else None

    if "children" in includes:
        data["children"] = block.children if hasattr(block, 'children') else []  # List of usage keys of children

    if "editable_children" in includes:
        # "Editable children" means children in the same bundle, as opposed to linked children in other bundles.
        data["editable_children"] = []
        child_includes = block.runtime.child_includes_of(block)
        for idx, include in enumerate(child_includes):
            if include.link_id is None:
                data["editable_children"].append(block.children[idx])

    return data


def xblock_type_display_name(block_type):
    """
    Get the display name for the specified XBlock class.
    """
    try:
        # We want to be able to give *some* value, even if the XBlock is later
        # uninstalled.
        block_class = XBlock.load_class(block_type)
    except PluginMissingError:
        return block_type

    if hasattr(block_class, 'display_name') and block_class.display_name.default:
        return _(block_class.display_name.default)  # pylint: disable=translation-of-non-string
    else:
        return block_type  # Just use the block type as the name


def get_block_display_name(block: XBlock) -> str:
    """
    Get the display name from an instatiated XBlock, falling back to the XBlock-type-defined-default.
    """
    display_name = getattr(block, "display_name", None)
    if display_name is not None:
        return display_name
    else:
        return xblock_type_display_name(block.scope_ids.block_type)


def get_component_from_usage_key(usage_key: UsageKeyV2) -> Component:
    """
    Fetch the Component object for a given usage key.

    Raises a ObjectDoesNotExist error if no such Component exists.

    This is a lower-level function that will return a Component even if there is
    no current draft version of that Component (because it's been soft-deleted).
    """
    learning_package = authoring_api.get_learning_package_by_key(
        str(usage_key.context_key)
    )
    return authoring_api.get_component_by_key(
        learning_package.id,
        namespace='xblock.v1',
        type_name=usage_key.block_type,
        local_key=usage_key.block_id,
    )


def get_block_olx(
    usage_key: UsageKeyV2,
    *,
    version: int | LatestVersion = LatestVersion.AUTO
) -> str:
    """
    Get the OLX source of the of the given Learning-Core-backed XBlock and a version.
    """
    component = get_component_from_usage_key(usage_key)
    version = get_auto_latest_version(version)

    if version == LatestVersion.DRAFT:
        component_version = component.versioning.draft
    elif version == LatestVersion.PUBLISHED:
        component_version = component.versioning.published
    else:
        assert isinstance(version, int)
        component_version = component.versioning.version_num(version)
    if component_version is None:
        raise NoSuchUsage(usage_key)

    # TODO: we should probably make a method on ComponentVersion that returns
    # a content based on the name. Accessing by componentversioncontent__key is
    # awkward.
    content = component_version.contents.get(componentversioncontent__key="block.xml")

    return content.text


def get_block_draft_olx(usage_key: UsageKeyV2) -> str:
    """ DEPRECATED. Use get_block_olx(). Can be removed post-Teak. """
    return get_block_olx(usage_key, version=LatestVersion.DRAFT)


def render_block_view(block, view_name, user):  # pylint: disable=unused-argument
    """
    Get the HTML, JS, and CSS needed to render the given XBlock view.

    The only difference between this method and calling
        load_block().render(view_name)
    is that this method can fall back from 'author_view' to 'student_view'

    Returns a Fragment.
    """
    try:
        fragment = block.render(view_name)
    except NoSuchViewError:
        fallback_view = None
        if view_name == 'author_view':
            fallback_view = 'student_view'
        if fallback_view:
            fragment = block.render(fallback_view)
        else:
            raise

    return fragment


def get_handler_url(
    usage_key: UsageKeyV2,
    handler_name: str,
    user: UserType | None,
    *,
    version: int | LatestVersion = LatestVersion.AUTO,
):
    """
    A method for getting the URL to any XBlock handler. The URL must be usable
    without any authentication (no cookie, no OAuth/JWT), and may expire. (So
    that we can render the XBlock in a secure IFrame without any access to
    existing cookies.)

    The returned URL will contain the provided handler_name, but is valid for
    any other handler on the same XBlock. Callers may replace any occurrences of
    the handler name in the resulting URL with the name of any other handler and
    the URL will still work. (This greatly reduces the number of calls to this
    API endpoint that are needed to interact with any given XBlock.)

    Params:
        usage_key       - Usage Key (Opaque Key object or string)
        handler_name    - Name of the handler or a dummy name like 'any_handler'
        user            - Django User (registered or anonymous)
        version         - Run the handler against a specific version of the
                          block (e.g. when viewing an old version of it in
                          Studio). Some blocks use handlers to load their data
                          so it's important the handler matches the student_view
                          etc.

    This view does not check/care if the XBlock actually exists.
    """
    site_root_url = get_xblock_app_config().get_site_root_url()
    if not user:
        raise TypeError("Cannot get handler URLs without specifying a specific user ID.")
    if user.is_authenticated:
        user_id = user.id
    elif user.is_anonymous:
        user_id = get_xblock_id_for_anonymous_user(user)
    else:
        raise ValueError("Invalid user value")
    # Now generate a token-secured URL for this handler, specific to this user
    # and this XBlock:
    secure_token = get_secure_token_for_xblock_handler(user_id, str(usage_key))
    # Now generate the URL to that handler:
    kwargs = {
        'usage_key': usage_key,
        'user_id': user_id,
        'secure_token': secure_token,
        'handler_name': handler_name,
    }
    if version != LatestVersion.AUTO:
        kwargs["version"] = version
    path = reverse('xblock_api:xblock_handler', kwargs=kwargs)

    # We must return an absolute URL. We can't just use
    # rest_framework.reverse.reverse to get the absolute URL because this method
    # can be called by the XBlock from python as well and in that case we don't
    # have access to the request.
    return site_root_url + path


from django.template.defaultfilters import filesizeformat
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore import BlockData
from xmodule.modulestore.split_mongo import BlockKey
from datetime import datetime, timezone
import bson
from bson.codec_options import CodecOptions
import zlib

from .models import LearningCoreCourseStructure

def get_structure_for_course(course_key: CourseKey):
    """Just gets the published version for now, need to update to do both branches later"""
    lccs = LearningCoreCourseStructure.objects.get(course_key=course_key)
    uncompressed_data = zlib.decompress(lccs.structure)
    return bson.decode(uncompressed_data, codec_options=CodecOptions(tz_aware=True))

def update_learning_core_course(course_key: CourseKey):
    """
    This is going to write to LearningCoreCourseStructure.

    Pass 0 of this: just push hardcoded data into the shim

    """
    writer = LearningCoreCourseShimWriter()
    structure = writer.make_structure()

    import pprint

    #encoded = bson.encode(structure)
    #decoded = bson.decode(encoded)

    with open("lc_struct.txt", "w") as struct_file:
        printer = pprint.PrettyPrinter(indent=2, stream=struct_file)
        # printer.pprint(decoded)
        printer.pprint(structure)

    # Structure doc is so repetitive that we get a 4-5X reduction in file size
    num_blocks = len(structure['blocks'])
    encoded_structure = zlib.compress(bson.encode(structure, codec_options=CodecOptions(tz_aware=True)))

    lccs, _created = LearningCoreCourseStructure.objects.get_or_create(course_key=course_key)
    lccs.structure = encoded_structure
    lccs.save()

    log.info(f"Updated Learning Core Structure (for Split) on course {course_key}.")
    log.info(f"Structure size: {filesizeformat(len(encoded_structure))} for {num_blocks} blocks.")


import pytz

class LearningCoreCourseShimWriter:
    def __init__(self):
        self.structure_obj_id = bson.ObjectId()

        # Can't use stdlib's timezone.utc, because of various comparisons we
        # need to make (can't mix offset types)
        self.edited_on = datetime.now(tz=timezone.utc)
        self.user_id = -1  # This is "the system did it"

    def make_structure(self):
        structure = self.base_structure()
        course_entry = self.course_block_entry()

        structure['blocks'].append(course_entry)
        structure['blocks'].extend(self.non_child_blocks())
        chapter_1 = self.base_block_entry("chapter", "cf67a98624214ef1ac158378ee103f8c")
        chapter_1['definition'] = bson.ObjectId('68508b48bd8f1408c3839ded')
        chapter_1['fields'] = {
            'children': [
                ['sequential', '153b0bbfafa545239df5ee11c12f6c9b']
            ],
            'display_name': 'First Section',
        }
        structure['blocks'].append(chapter_1)
        seq_1 = self.base_block_entry('sequential', '153b0bbfafa545239df5ee11c12f6c9b')
        seq_1['fields'] = {
            'children': [
                ['vertical', 'e3af9b9bbd144102862d30067d7cf4fb'],
            ],
            'display_name': 'First Subsection',
        }
        seq_1['definition'] = bson.ObjectId('68508b56bd8f1408c3839df2')
        structure['blocks'].append(seq_1)

        vertical_1 = self.base_block_entry('vertical', 'e3af9b9bbd144102862d30067d7cf4fb')
        vertical_1['fields'] = {
            'children': [
                ['problem', '2f14f0bd726d488cb9221b60cb735183']
            ],
            'display_name': 'Check Your Understanding',
        }
        vertical_1['definition'] = bson.ObjectId('68508b97bd8f1408c3839dfd'),
        structure['blocks'].append(vertical_1)

        problem_1 = self.base_block_entry('problem', '2f14f0bd726d488cb9221b60cb735183')
        problem_1['fields'] = {
            'children': [],
            'display_name': 'This is an LC Problem!',
            'markdown_edited': False,
            'rerandomize': 'never',
            'show_reset_button': False,
            'showanswer': 'finished',
            'weight': 1.0
        }
        problem_1['definition'] = bson.ObjectId('68508bd6bd8f1408c3839e01')
        structure['blocks'].append(problem_1)

        return structure

    def base_structure(self):
        doc_id = bson.ObjectId()

        return {
            '_id': doc_id,
            'blocks': [],
            'schema_version': 1,  # LOL

            'root': ['course', 'course'],  # Root is always the CourseBlock
            'edited_by': self.user_id,
            'edited_on': self.edited_on,

            # We're always going to be the "first" version for now, from Split's
            # perspective.
            'previous_version': None,
            'original_version': doc_id
        }

    def course_block_entry(self):
        entry = self.base_block_entry('course', 'course')
        entry['fields'] = {
            'allow_anonymous': True,
            'allow_anonymous_to_peers': False,
            'cert_html_view_enabled': True,
            'children': [
                ['chapter', 'cf67a98624214ef1ac158378ee103f8c']
            ],
            'discussion_blackouts': [],
            'discussion_topics': {'General': {'id': 'course'}},
            'discussions_settings': {
                'enable_graded_units': False,
                'enable_in_context': True,
                'openedx': { 'group_at_subsection': False},
                'posting_restrictions': 'disabled',
                'provider_type': 'openedx',
                'unit_level_visibility': True
            },
            'display_name': 'Just a Demo Course',
            'end': None,
            'language': 'en',

            ## HARDCODED START DATE
            'start': datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc),
            'static_asset_path': 'course',
            'tabs': [
                {
                    'course_staff_only': False,
                    'name': 'Course',
                    'type': 'courseware'
                },
                {
                    'course_staff_only': False,
                    'name': 'Progress',
                    'type': 'progress'
                },
                {
                    'course_staff_only': False,
                    'name': 'Dates',
                    'type': 'dates'
                },
                {
                    'course_staff_only': False,
                    'name': 'Discussion',
                    'type': 'discussion'
                },
                {
                    'course_staff_only': False,
                    'is_hidden': True,
                    'name': 'Wiki',
                    'type': 'wiki'
                },
                {
                    'course_staff_only': False,
                    'name': 'Textbooks',
                    'type': 'textbooks'
                }
            ],
            'xml_attributes': {
                'filename': [ 'course/2025-02-24.xml', 'course/2025-02-24.xml']
            },
        }
        entry['definition'] = bson.ObjectId('68508b38bd8f1408c3839dc1')
        return entry

    def base_block_entry(self, block_type: str, block_id: str, definition=None):
        return {
            'asides': {},  # We are *so* not doing asides in this prototype
            'block_id': block_id,
            'block_type': block_type,
            'defaults': {},
            'fields': {'children': []},  # Even blocks without children are written this way.
            'definition': definition or bson.ObjectId(),
            'edit_info': self.base_edit_info()
        }


    def base_edit_info(self):
        return {
            'edited_by': self.user_id,
            'edited_on': self.edited_on,

            # This is v1 libraries data that we're faking
            'original_usage': None,
            'original_usage_vesion': None,

            # Edit history, all of which we're faking
            'previous_version': None,
            'source_version': self.structure_obj_id,
            'update_version': self.structure_obj_id,
        }

    def non_child_blocks(self):
        from bson import ObjectId
        """These are all the random blocks that are not connected to the course root"""
        # def: ObjectId('67ddbd4880aff2c029322017')
        overview = self.base_block_entry('about', 'overview', ObjectId('67ddbd4880aff2c029322017'))

        # def: ObjectId('68508b10bd8f1408c3839dbe')
        updates = self.base_block_entry('course_info', 'updates', ObjectId('68508b10bd8f1408c3839dbe'))

        # def: ObjectId('68508b38bd8f1408c3839dc4')
        title = self.base_block_entry('about', 'title', ObjectId('68508b38bd8f1408c3839dc4'))

        # def: ObjectId('68508b39bd8f1408c3839dc7')
        subtitle = self.base_block_entry('about', 'subtitle', ObjectId('68508b39bd8f1408c3839dc7'))

        # def: ObjectId('68508b39bd8f1408c3839dca')
        duration = self.base_block_entry('about', 'duration', ObjectId('68508b39bd8f1408c3839dca'))

        # def: ObjectId('68508b3abd8f1408c3839dcd')
        description = self.base_block_entry('about', 'description', ObjectId('68508b3abd8f1408c3839dcd'))

        # def: ObjectId('68508b3abd8f1408c3839dd0')
        short_description = self.base_block_entry('about', 'short_description', ObjectId('68508b3abd8f1408c3839dd0'))

        # I have so many questions about entrance exams...

        # def: ObjectId('68508b3cbd8f1408c3839dd6')
        entrance_exam_enabled = self.base_block_entry('about', 'entrance_exam_enabled', ObjectId('68508b3cbd8f1408c3839dd6'))

        # def: ObjectId('68508b3cbd8f1408c3839dd9')
        entrance_exam_id = self.base_block_entry('about', 'entrance_exam_id', ObjectId('68508b3cbd8f1408c3839dd9'))

        # def: ObjectId('68508b3dbd8f1408c3839ddc')
        entrance_exam_minimum_score_pct = self.base_block_entry('about', 'entrance_exam_minimum_score_pct', ObjectId('68508b3dbd8f1408c3839ddc'))

        # def: ObjectId('68508b3ebd8f1408c3839ddf')
        about_sidebar_html = self.base_block_entry('about', 'about_sidebar_html', ObjectId('68508b3ebd8f1408c3839ddf'))

        return [
            overview,
            updates,
            title,
            subtitle,
            duration,
            description,
            short_description,
            entrance_exam_enabled,
            entrance_exam_id,
            entrance_exam_minimum_score_pct,
            about_sidebar_html,
        ]