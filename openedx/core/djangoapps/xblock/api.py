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
from openedx_learning.api.authoring_models import Component, ComponentVersion, ContainerVersion, PublishLog
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
from bson import ObjectId
from bson.codec_options import CodecOptions
import zlib
from openedx.core.lib.cache_utils import request_cached


from .models import (
    LearningCoreCourseStructure,
    LearningCoreLearningContext,
    XBlockVersionFieldData,
)

def get_structure_for_course(course_key: CourseKey):
    """Just gets the published version for now, need to update to do both branches later"""
    lookup_key = course_key.replace(branch=None, version_guid=None)
    lccs = LearningCoreCourseStructure.objects.get(course_key=lookup_key)
    uncompressed_data = zlib.decompress(lccs.structure)
    return bson.decode(uncompressed_data, codec_options=CodecOptions(tz_aware=True))


def update_learning_core_course(course_key: CourseKey):
    """
    This is going to write to LearningCoreCourseStructure.

    Pass 0 of this: just push hardcoded data into the shim

    """
    writer = LearningCoreCourseShimWriter(course_key)
    structure = writer.make_structure()

    import pprint

    with open("lc_struct.txt", "w") as struct_file:
        printer = pprint.PrettyPrinter(indent=2, stream=struct_file)
        printer.pprint(structure)

    # Structure doc is so repetitive that we get a 4-5X reduction in file size
    num_blocks = len(structure['blocks'])
    encoded_structure = zlib.compress(bson.encode(structure, codec_options=CodecOptions(tz_aware=True)))

    lccs, _created = LearningCoreCourseStructure.objects.get_or_create(course_key=course_key)
    lccs.structure = encoded_structure
    lccs.save()

    log.info(f"Updated Learning Core Structure (for Split) on course {course_key}.")
    log.info(f"Structure size: {filesizeformat(len(encoded_structure))} for {num_blocks} blocks.")

    from xmodule.modulestore.django import SignalHandler
    log.info(f"Emitting course_published signal for {course_key}")
    SignalHandler.course_published.send_robust(sender=update_learning_core_course, course_key=course_key)


@request_cached()
def learning_core_backend_enabled_for_course(course_key: CourseKey):
    try:
        lookup_key = course_key.replace(branch=None, version_guid=None)
        lc_context = LearningCoreLearningContext.objects.get(key=lookup_key)
        return lc_context.use_learning_core
    except LearningCoreLearningContext.DoesNotExist:
        return False


def get_definition_doc(def_id: ObjectId):
    try:
        xb_field_data = XBlockVersionFieldData.objects.get(definition_object_id=str(def_id))
    except XBlockVersionFieldData.DoesNotExist:
        return None

    return {
        '_id': ObjectId(xb_field_data.definition_object_id),
        'block_type': None,
        'fields': xb_field_data.content,
        'edit_info': {
            'edited_by': xb_field_data.publishable_entity_version.created_by_id,
            'edited_on': xb_field_data.publishable_entity_version.created,

            # These are supposed to be the ObjectIds of the structure docs that
            # represent the last time this block was edited and the original
            # version at the time of creation. It's actually a common occurrence
            # for these values to get pruned in Split, so we're making dummy
            # ObjectIds--i.e. we're making it look like this was created a while
            # ago and the versions for both the original creation and last
            # update are no longer available.
            'previous_version': ObjectId(),
            'original_version': ObjectId(),
        },
        'schema_version': 1,
    }


def handle_library_publish(publish_log: PublishLog):
    affected_course_keys = set(
        key
        for key in publish_log.records.values_list('entity__block__learning_context__key', flat=True)
        if key
    )
    log.info(f"Affected Courses to update in LC shim: {affected_course_keys}")
    for course_key in affected_course_keys:
        log.info(f"Type of course_key: {type(course_key)}")
        update_learning_core_course(course_key)


def create_xblock_field_data_for_container(version: ContainerVersion):
    # this whole thing should be in xblock.api instead of here.
    from openedx.core.djangoapps.xblock.models import Block

    entity = version.publishable_entity_version.entity

    # If this PublishableEntity isn't associated with an Learning Core backed
    # XBlock, then we can't write anything. Note: This is going to be an edge
    # case later, when we want to add an existing container to a container that
    # was imported from a course.
    if not hasattr(entity, 'block'):
        log.error(f"No Block detected for entity {entity.key}???")
        return

    parent_block = entity.block
    container_usage_key = parent_block.key
    course_key = container_usage_key.course_key

    # Generic values for all container types
    content_scoped_fields = {}
    settings_scoped_fields = {
        'display_name': version.publishable_entity_version.title
    }
    children = []

    # Things specific to the course root...
    if container_usage_key.block_type == "course":
        content_scoped_fields['license'] = None
        content_scoped_fields['wiki_slug'] = f'{course_key.org}.{course_key.course}.{course_key.run}'
        settings_scoped_fields.update(
            _course_block_entry(container_usage_key)
        )

    for child_entity_row in version.entity_list.entitylistrow_set.select_related('entity__block').all():
        log.info(f"Iterating children: {child_entity_row.entity}")

        # If it's not a container and it doesn't have field data, we won't know what to do with it in the structure doc,
        # so just skip it. This can happen when you have OLX with no corresponding XBlock class.
        if not hasattr(child_entity_row.entity, 'container') and not hasattr(child_entity_row.entity, 'xblockfielddata'):
            continue

        if not hasattr(child_entity_row.entity, 'block'):
            # This can happen if we add a new component in a library to a
            # container that was imported from a course.
            match(container_usage_key.block_type):
                case "course":
                    child_block_type = "chapter"
                    child_block_id = child_entity_row.entity.key
                case "chapter":
                    child_block_type = "sequential"
                    child_block_id = child_entity_row.entity.key
                case "sequential":
                    child_block_type = "vertical"
                    child_block_id = child_entity_row.entity.key
                case "vertical":
                    child_block_type = child_entity_row.entity.component.component_type.name
                    child_block_id = child_entity_row.entity.component.local_key

            log.info(f"Creating child usage key: {child_usage_key}")
            child_usage_key = course_key.make_usage_key(child_block_type, child_block_id)
            child_block = Block.objects.create(
                learning_context_id=parent_block.learning_context_id,
                entity=child_entity_row.entity,
                key=child_usage_key,
            )
        else:
            child_block = child_entity_row.entity.block
            child_usage_key = child_block.key

        if child_usage_key.block_type != "discussion":
            children.append(
                [child_usage_key.block_type, child_usage_key.block_id]
            )

    field_data = XBlockVersionFieldData.objects.create(
        pk=version.pk,
        content=content_scoped_fields,
        settings=settings_scoped_fields,
        children=children,
    )
    log.info(f"Wrote XBlock Data for Container: {version}: {field_data}")


def _course_block_entry(usage_key):
    return {
        'allow_anonymous': True,
        'allow_anonymous_to_peers': False,
        'cert_html_view_enabled': True,
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
            'filename': [ f'course/{usage_key.run}.xml', f'course/{usage_key.run}.xml']
        }
    }


class LearningCoreCourseShimWriter:
    def __init__(self, course_key: CourseKey):
        self.course_key = course_key
        self.structure_obj_id = bson.ObjectId()

        self.edited_on = datetime.now(tz=timezone.utc)
        self.user_id = -1  # This is "the system did it"

    def make_structure(self):
        structure = self.base_structure()

        context = LearningCoreLearningContext.objects.get(key=self.course_key)
        blocks = (
            context.blocks
                   .select_related(
                       'entity__published__version__xblockversionfielddata',
                       'entity__draft__version__xblockversionfielddata',
                    )
        )
        for block in blocks:
            entity_version = block.entity.published.version
            if not hasattr(entity_version, 'xblockversionfielddata'):
                log.error(f"MISSING XBlockVersionFieldData for {block.key}")
                continue  # Just give up on this block.

            if block.key.block_type == "discussion":
                # hacky hacky prototype...
                log.error(f"Skipping discussion block {block.key} because we don't seem to handle inline discussions right")
                continue

            field_data = entity_version.xblockversionfielddata
            block_entry = self.base_block_entry(
                block.key.block_type,
                block.key.block_id,
                ObjectId(field_data.definition_object_id),
            )
            block_entry['fields'].update(field_data.settings)

            # This is a hack for when discussion data's already gotten into our saved children, even though we don't
            # have any field data associated with it.
            if field_data.children:
                filtered_children = [
                    entry for entry in field_data.children if entry[0] != "discussion"
                ]
                if filtered_children:
                    block_entry['fields']['children'] = filtered_children

            structure['blocks'].append(block_entry)

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

    def base_block_entry(self, block_type: str, block_id: str, definition_object_id: ObjectId):
        return {
            'asides': {},  # We are *so* not doing asides in this prototype
            'block_id': block_id,
            'block_type': block_type,
            'defaults': {},
            'fields': {'children': []},  # Even blocks without children are written this way.
            'definition': definition_object_id,
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
