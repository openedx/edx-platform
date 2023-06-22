"""
Service functions for xblock views, as found in:

- contentstore/views/block.py
- rest_api/v1/viewx/xblock.py

We extracted all the logic from the `xblock_handler` endpoint that lives in
contentstore/views/block.py to this file, because the logic is reused in another view now.
Along with it, we moved the business logic of the other views in that file, since that is related.
"""

import logging
from datetime import datetime
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import (User)  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.utils.timezone import timezone
from django.utils.translation import gettext as _
from openedx_events.content_authoring.data import DuplicatedXBlockData
from openedx_events.content_authoring.signals import XBLOCK_DUPLICATED
from edx_proctoring.api import (
    get_exam_by_content_id,
)
from edx_proctoring.exceptions import ProctoredExamNotFoundException
from lti_consumer.models import CourseAllowPIISharingInLTIFlag
from opaque_keys.edx.locator import LibraryUsageLocator
from pytz import UTC
from xblock.fields import Scope

from common.djangoapps.edxmako.services import MakoService
from common.djangoapps.student.auth import (
    has_studio_read_access,
    has_studio_write_access,
)
from common.djangoapps.util.date_utils import get_default_time_display
from common.djangoapps.util.json_request import JsonResponse, expect_json
from common.djangoapps.xblock_django.user_service import DjangoXBlockUserService
from openedx.core.djangoapps.bookmarks import api as bookmarks_api
from openedx.core.lib.gating import api as gating_api
from openedx.core.toggles import ENTRANCE_EXAMS
from xmodule.course_block import (
    DEFAULT_START_DATE,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.library_tools import (
    LibraryToolsService,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import (
    modulestore,
)  # lint-amnesty, pylint: disable=wrong-import-order

from xmodule.modulestore.inheritance import (
    own_metadata,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.services import (
    ConfigurationService,
    SettingsService,
    TeamsConfigurationService,
)  # lint-amnesty, pylint: disable=wrong-import-order

from ..utils import (
    find_release_date_source,
    find_staff_lock_source,
    has_children_visible_to_specific_partition_groups,
    is_currently_visible_to_students,
)

from ..helpers import (
    import_staged_content_from_user_clipboard,
    xblock_type_display_name,
)
from .usage_key_with_run import usage_key_with_run
from .create_xblock import create_xblock

log = logging.getLogger(__name__)

CREATE_IF_NOT_FOUND = ["course_info"]

# Useful constants for defining predicates
NEVER = lambda x: False
ALWAYS = lambda x: True

__all__ = [
    "load_services_for_studio",
]


def _filter_entrance_exam_grader(graders):
    """
    If the entrance exams feature is enabled we need to hide away the grader from
    views/controls like the 'Grade as' dropdown that allows a course author to select
    the grader type for a given section of a course
    """
    if ENTRANCE_EXAMS.is_enabled():
        graders = [
            grader for grader in graders if grader.get("type") != "Entrance Exam"
        ]
    return graders


def _is_library_component_limit_reached(usage_key):
    """
    Verify if the library has reached the maximum number of components allowed in it
    """
    store = modulestore()
    parent = store.get_item(usage_key)
    if not parent.has_children:
        # Limit cannot be applied on such items
        return False
    total_children = len(parent.children)
    return total_children + 1 > settings.MAX_BLOCKS_PER_CONTENT_LIBRARY


class StudioPermissionsService:
    """
    Service that can provide information about a user's permissions.

    Deprecated. To be replaced by a more general authorization service.

    Only used by LibraryContentBlock (and library_tools.py).
    """
    def __init__(self, user):
        self._user = user

    def can_read(self, course_key):
        """Does the user have read access to the given course/library?"""
        return has_studio_read_access(self._user, course_key)

    def can_write(self, course_key):
        """Does the user have read access to the given course/library?"""
        return has_studio_write_access(self._user, course_key)


def load_services_for_studio(runtime, user):
    """
    Function to set some required services used for XBlock edits and studio_view.
    (i.e. whenever we're not loading _prepare_runtime_for_preview.) This is required to make information
    about the current user (especially permissions) available via services as needed.
    """
    services = {
        "user": DjangoXBlockUserService(user),
        "studio_user_permissions": StudioPermissionsService(user),
        "mako": MakoService(),
        "settings": SettingsService(),
        "lti-configuration": ConfigurationService(CourseAllowPIISharingInLTIFlag),
        "teams_configuration": TeamsConfigurationService(),
        "library_tools": LibraryToolsService(modulestore(), user.id),
    }

    runtime._services.update(services)  # lint-amnesty, pylint: disable=protected-access


def _update_with_callback(xblock, user, old_metadata=None, old_content=None):
    """
    Updates the xblock in the modulestore.
    But before doing so, it calls the xblock's editor_saved callback function.
    """
    if callable(getattr(xblock, "editor_saved", None)):
        if old_metadata is None:
            old_metadata = own_metadata(xblock)
        if old_content is None:
            old_content = xblock.get_explicitly_set_fields_by_scope(Scope.content)
        load_services_for_studio(xblock.runtime, user)
        xblock.editor_saved(user, old_metadata, old_content)

    # Update after the callback so any changes made in the callback will get persisted.
    return modulestore().update_item(xblock, user.id)


@login_required
@expect_json
def create_item(request):
    """
    Exposes internal helper method without breaking existing bindings/dependencies
    """
    return _create_block(request)


@login_required
@expect_json
def _create_block(request):
    """View for create blocks."""
    parent_locator = request.json["parent_locator"]
    usage_key = usage_key_with_run(parent_locator)
    if not has_studio_write_access(request.user, usage_key.course_key):
        raise PermissionDenied()

    if request.json.get("staged_content") == "clipboard":
        # Paste from the user's clipboard (content_staging app clipboard, not browser clipboard) into 'usage_key':
        try:
            created_xblock = import_staged_content_from_user_clipboard(
                parent_key=usage_key, request=request
            )
        except Exception:  # pylint: disable=broad-except
            log.exception(
                "Could not paste component into location {}".format(usage_key)
            )
            return JsonResponse(
                {"error": _("There was a problem pasting your component.")}, status=400
            )
        if created_xblock is None:
            return JsonResponse(
                {"error": _("Your clipboard is empty or invalid.")}, status=400
            )
        return JsonResponse(
            {
                "locator": str(created_xblock.location),
                "courseKey": str(created_xblock.location.course_key),
            }
        )

    category = request.json["category"]
    if isinstance(usage_key, LibraryUsageLocator):
        # Only these categories are supported at this time.
        if category not in ["html", "problem", "video"]:
            return HttpResponseBadRequest(
                "Category '%s' not supported for Libraries" % category,
                content_type="text/plain",
            )

        if _is_library_component_limit_reached(usage_key):
            return JsonResponse(
                {
                    "error": _(
                        "Libraries cannot have more than {limit} components"
                    ).format(limit=settings.MAX_BLOCKS_PER_CONTENT_LIBRARY)
                },
                status=400,
            )

    created_block = create_xblock(
        parent_locator=parent_locator,
        user=request.user,
        category=category,
        display_name=request.json.get("display_name"),
        boilerplate=request.json.get("boilerplate"),
    )

    return JsonResponse(
        {
            "locator": str(created_block.location),
            "courseKey": str(created_block.location.course_key),
        }
    )


def _get_source_index(source_usage_key, source_parent):
    """
    Get source index position of the XBlock.

    Arguments:
        source_usage_key (BlockUsageLocator): Locator of source item.
        source_parent (XBlock): A parent of the source XBlock.

    Returns:
        source_index (int): Index position of the xblock in a parent.
    """
    try:
        source_index = source_parent.children.index(source_usage_key)
        return source_index
    except ValueError:
        return None


def _duplicate_block(
    parent_usage_key,
    duplicate_source_usage_key,
    user,
    display_name=None,
    is_child=False,
):
    """
    Duplicate an existing xblock as a child of the supplied parent_usage_key.
    """
    store = modulestore()
    with store.bulk_operations(duplicate_source_usage_key.course_key):
        source_item = store.get_item(duplicate_source_usage_key)
        # Change the blockID to be unique.
        dest_usage_key = source_item.location.replace(name=uuid4().hex)
        category = dest_usage_key.block_type

        # Update the display name to indicate this is a duplicate (unless display name provided).
        # Can't use own_metadata(), b/c it converts data for JSON serialization -
        # not suitable for setting metadata of the new block
        duplicate_metadata = {}
        for field in source_item.fields.values():
            if field.scope == Scope.settings and field.is_set_on(source_item):
                duplicate_metadata[field.name] = field.read_from(source_item)

        if is_child:
            display_name = (
                display_name or source_item.display_name or source_item.category
            )

        if display_name is not None:
            duplicate_metadata["display_name"] = display_name
        else:
            if source_item.display_name is None:
                duplicate_metadata["display_name"] = _("Duplicate of {0}").format(
                    source_item.category
                )
            else:
                duplicate_metadata["display_name"] = _("Duplicate of '{0}'").format(
                    source_item.display_name
                )

        asides_to_create = []
        for aside in source_item.runtime.get_asides(source_item):
            for field in aside.fields.values():
                if field.scope in (
                    Scope.settings,
                    Scope.content,
                ) and field.is_set_on(aside):
                    asides_to_create.append(aside)
                    break

        for aside in asides_to_create:
            for field in aside.fields.values():
                if field.scope not in (
                    Scope.settings,
                    Scope.content,
                ):
                    field.delete_from(aside)

        dest_block = store.create_item(
            user.id,
            dest_usage_key.course_key,
            dest_usage_key.block_type,
            block_id=dest_usage_key.block_id,
            definition_data=source_item.get_explicitly_set_fields_by_scope(
                Scope.content
            ),
            metadata=duplicate_metadata,
            runtime=source_item.runtime,
            asides=asides_to_create,
        )

        children_handled = False

        if hasattr(dest_block, "studio_post_duplicate"):
            # Allow an XBlock to do anything fancy it may need to when duplicated from another block.
            # These blocks may handle their own children or parenting if needed. Let them return booleans to
            # let us know if we need to handle these or not.
            load_services_for_studio(dest_block.runtime, user)
            children_handled = dest_block.studio_post_duplicate(store, source_item)

        # Children are not automatically copied over (and not all xblocks have a 'children' attribute).
        # Because DAGs are not fully supported, we need to actually duplicate each child as well.
        if source_item.has_children and not children_handled:
            dest_block.children = dest_block.children or []
            for child in source_item.children:
                dupe = _duplicate_block(
                    dest_block.location, child, user=user, is_child=True
                )
                if (
                    dupe not in dest_block.children
                ):  # _duplicate_block may add the child for us.
                    dest_block.children.append(dupe)
            store.update_item(dest_block, user.id)

        # pylint: disable=protected-access
        if "detached" not in source_item.runtime.load_block_type(category)._class_tags:
            parent = store.get_item(parent_usage_key)
            # If source was already a child of the parent, add duplicate immediately afterward.
            # Otherwise, add child to end.
            if source_item.location in parent.children:
                source_index = parent.children.index(source_item.location)
                parent.children.insert(source_index + 1, dest_block.location)
            else:
                parent.children.append(dest_block.location)
            store.update_item(parent, user.id)

        # .. event_implemented_name: XBLOCK_DUPLICATED
        XBLOCK_DUPLICATED.send_event(
            time=datetime.now(timezone.utc),
            xblock_info=DuplicatedXBlockData(
                usage_key=dest_block.location,
                block_type=dest_block.location.block_type,
                source_usage_key=duplicate_source_usage_key,
            ),
        )

        return dest_block.location


@login_required
@expect_json
def delete_item(request, usage_key):
    """
    Exposes internal helper method without breaking existing bindings/dependencies
    """
    _delete_item(usage_key, request.user)


def _delete_item(usage_key, user):
    """
    Deletes an existing xblock with the given usage_key.
    If the xblock is a Static Tab, removes it from course.tabs as well.
    """
    store = modulestore()

    with store.bulk_operations(usage_key.course_key):
        # VS[compat] cdodge: This is a hack because static_tabs also have references from the course block, so
        # if we add one then we need to also add it to the policy information (i.e. metadata)
        # we should remove this once we can break this reference from the course to static tabs
        if usage_key.block_type == "static_tab":
            course = store.get_course(usage_key.course_key)
            existing_tabs = course.tabs or []
            course.tabs = [
                tab
                for tab in existing_tabs
                if tab.get("url_slug") != usage_key.block_id
            ]
            store.update_item(course, user.id)

        # Delete user bookmarks
        bookmarks_api.delete_bookmarks(usage_key)
        store.delete_item(usage_key, user.id)


def _get_gating_info(course, xblock):
    """
    Returns a dict containing gating information for the given xblock which
    can be added to xblock info responses.

    Arguments:
        course (CourseBlock): The course
        xblock (XBlock): The xblock

    Returns:
        dict: Gating information
    """
    info = {}
    if xblock.category == "sequential" and course.enable_subsection_gating:
        if not hasattr(course, "gating_prerequisites"):
            # Cache gating prerequisites on course block so that we are not
            # hitting the database for every xblock in the course
            course.gating_prerequisites = gating_api.get_prerequisites(course.id)
        info["is_prereq"] = gating_api.is_prerequisite(course.id, xblock.location)
        info["prereqs"] = [
            p
            for p in course.gating_prerequisites
            if str(xblock.location) not in p["namespace"]
        ]
        (
            prereq,
            prereq_min_score,
            prereq_min_completion,
        ) = gating_api.get_required_content(course.id, xblock.location)
        info["prereq"] = prereq
        info["prereq_min_score"] = prereq_min_score
        info["prereq_min_completion"] = prereq_min_completion
        if prereq:
            info["visibility_state"] = VisibilityState.gated
    return info


def _was_xblock_ever_exam_linked_with_external(course, xblock):
    """
    Determine whether this XBlock is or was ever configured as an external proctored exam.

    If this block is *not* currently an externally linked proctored exam, the best way for us to tell
    whether it was was *ever* such is by checking whether
    edx-proctoring has an exam record associated with the block's ID,
    and the exam record has external_id.
    If an exception is not raised, then we know that such a record exists,
    indicating that this *was* once an externally linked proctored exam.

    Arguments:
        course (CourseBlock)
        xblock (XBlock)

    Returns: bool
    """
    try:
        exam = get_exam_by_content_id(course.id, xblock.location)
        return bool("external_id" in exam and exam["external_id"])
    except ProctoredExamNotFoundException:
        pass
    return False


def add_container_page_publishing_info(xblock, xblock_info):
    """
    Adds information about the xblock's publish state to the supplied
    xblock_info for the container page.
    """

    def safe_get_username(user_id):
        """
        Guard against bad user_ids, like the infamous "**replace_user**".
        Note that this will ignore our special known IDs (ModuleStoreEnum.UserID).
        We should consider adding special handling for those values.

        :param user_id: the user id to get the username of
        :return: username, or None if the user does not exist or user_id is None
        """
        if user_id:
            try:
                return User.objects.get(id=user_id).username
            except:  # pylint: disable=bare-except
                pass

        return None

    xblock_info["edited_by"] = safe_get_username(xblock.subtree_edited_by)
    xblock_info["published_by"] = safe_get_username(xblock.published_by)
    xblock_info["currently_visible_to_students"] = is_currently_visible_to_students(
        xblock
    )
    xblock_info[
        "has_partition_group_components"
    ] = has_children_visible_to_specific_partition_groups(xblock)
    if xblock_info["release_date"]:
        xblock_info["release_date_from"] = _get_release_date_from(xblock)
    if xblock_info["visibility_state"] == VisibilityState.staff_only:
        xblock_info["staff_lock_from"] = _get_staff_lock_from(xblock)
    else:
        xblock_info["staff_lock_from"] = None


class VisibilityState:
    """
    Represents the possible visibility states for an xblock:

      live - the block and all of its descendants are live to students (excluding staff only items)
        Note: Live means both published and released.

      ready - the block is ready to go live and all of its descendants are live or ready (excluding staff only items)
        Note: content is ready when it is published and scheduled with a release date in the future.

      unscheduled - the block and all of its descendants have no release date (excluding staff only items)
        Note: it is valid for items to be published with no release date in which case they are still unscheduled.

      needs_attention - the block or its descendants are not fully live, ready or unscheduled
        (excluding staff only items)
        For example: one subsection has draft content, or there's both unreleased and released content in one section.

      staff_only - all of the block's content is to be shown to staff only
        Note: staff only items do not affect their parent's state.

      gated - all of the block's content is to be shown to students only after the configured prerequisite is met
    """

    live = "live"
    ready = "ready"
    unscheduled = "unscheduled"
    needs_attention = "needs_attention"
    staff_only = "staff_only"
    gated = "gated"


def _compute_visibility_state(
    xblock, child_info, is_unit_with_changes, is_course_self_paced=False
):
    """
    Returns the current publish state for the specified xblock and its children
    """
    if xblock.visible_to_staff_only:
        return VisibilityState.staff_only
    elif is_unit_with_changes:
        # Note that a unit that has never been published will fall into this category,
        # as well as previously published units with draft content.
        return VisibilityState.needs_attention

    is_unscheduled = xblock.start == DEFAULT_START_DATE
    is_live = is_course_self_paced or datetime.now(UTC) > xblock.start
    if child_info and child_info.get("children", []):
        all_staff_only = True
        all_unscheduled = True
        all_live = True
        for child in child_info["children"]:
            child_state = child["visibility_state"]
            if child_state == VisibilityState.needs_attention:
                return child_state
            elif not child_state == VisibilityState.staff_only:
                all_staff_only = False
                if not child_state == VisibilityState.unscheduled:
                    all_unscheduled = False
                    if not child_state == VisibilityState.live:
                        all_live = False
        if all_staff_only:
            return VisibilityState.staff_only
        elif all_unscheduled:
            return (
                VisibilityState.unscheduled
                if is_unscheduled
                else VisibilityState.needs_attention
            )
        elif all_live:
            return VisibilityState.live if is_live else VisibilityState.needs_attention
        else:
            return (
                VisibilityState.ready
                if not is_unscheduled
                else VisibilityState.needs_attention
            )
    if is_live:
        return VisibilityState.live
    elif is_unscheduled:
        return VisibilityState.unscheduled
    else:
        return VisibilityState.ready


def _get_release_date(xblock, user=None):
    """
    Returns the release date for the xblock, or None if the release date has never been set.
    """
    # If year of start date is less than 1900 then reset the start date to DEFAULT_START_DATE
    reset_to_default = False
    try:
        reset_to_default = xblock.start.year < 1900
    except ValueError:
        # For old mongo courses, accessing the start attribute calls `to_json()`,
        # which raises a `ValueError` for years < 1900.
        reset_to_default = True

    if reset_to_default and user:
        xblock.start = DEFAULT_START_DATE
        xblock = _update_with_callback(xblock, user)

    # Treat DEFAULT_START_DATE as a magic number that means the release date has not been set
    return (
        get_default_time_display(xblock.start)
        if xblock.start != DEFAULT_START_DATE
        else None
    )


def validate_and_update_xblock_due_date(xblock):
    """
    Validates the due date for the xblock, and set to None if pre-1900 due date provided
    """
    if xblock.due and xblock.due.year < 1900:
        xblock.due = None


def _get_release_date_from(xblock):
    """
    Returns a string representation of the section or subsection that sets the xblock's release date
    """
    return _xblock_type_and_display_name(find_release_date_source(xblock))


def _get_staff_lock_from(xblock):
    """
    Returns a string representation of the section or subsection that sets the xblock's release date
    """
    source = find_staff_lock_source(xblock)
    return _xblock_type_and_display_name(source) if source else None


def _xblock_type_and_display_name(xblock):
    """
    Returns a string representation of the xblock's type and display name
    """
    return _('{section_or_subsection} "{display_name}"').format(
        section_or_subsection=xblock_type_display_name(xblock),
        display_name=xblock.display_name_with_default,
    )
