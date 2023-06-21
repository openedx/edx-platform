"""
    Service with business logic supporting a view in handling an incoming xblock request.
    This method is used both by the internal xblock_handler API and by
    the public studio content API. The method handles GET, POST, PUT, PATCH, and DELETE requests.
"""



import logging
from datetime import datetime
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import (User)  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.timezone import timezone
from django.utils.translation import gettext as _
from edx_django_utils.plugins import pluggable_override
from openedx_events.content_authoring.data import DuplicatedXBlockData
from openedx_events.content_authoring.signals import XBLOCK_DUPLICATED
from edx_proctoring.api import (
    does_backend_support_onboarding,
    get_exam_by_content_id,
    get_exam_configuration_dashboard_url,
)
from edx_proctoring.exceptions import ProctoredExamNotFoundException
from help_tokens.core import HelpUrlExpert
from lti_consumer.models import CourseAllowPIISharingInLTIFlag
from opaque_keys.edx.locator import LibraryUsageLocator
from pytz import UTC
from xblock.core import XBlock
from xblock.fields import Scope

from cms.djangoapps.contentstore.config.waffle import SHOW_REVIEW_RULES_FLAG
from cms.djangoapps.models.settings.course_grading import CourseGradingModel
from common.djangoapps.edxmako.services import MakoService
from common.djangoapps.static_replace import replace_static_urls
from common.djangoapps.student.auth import (
    has_studio_read_access,
    has_studio_write_access,
)
from common.djangoapps.util.date_utils import get_default_time_display
from common.djangoapps.util.json_request import JsonResponse, expect_json
from common.djangoapps.xblock_django.user_service import DjangoXBlockUserService
from openedx.core.djangoapps.bookmarks import api as bookmarks_api
from openedx.core.djangoapps.discussions.models import DiscussionsConfiguration
from openedx.core.djangoapps.video_config.toggles import PUBLIC_VIDEO_SHARE
from openedx.core.lib.gating import api as gating_api
from openedx.core.toggles import ENTRANCE_EXAMS
from xmodule.course_block import (
    DEFAULT_START_DATE,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.library_tools import (
    LibraryToolsService,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore import (
    EdxJSONEncoder,
    ModuleStoreEnum,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import (
    modulestore,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.draft_and_published import (
    DIRECT_ONLY_CATEGORIES,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.exceptions import (
    InvalidLocationError,
    ItemNotFoundError,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.inheritance import (
    own_metadata,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.services import (
    ConfigurationService,
    SettingsService,
    TeamsConfigurationService,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.tabs import (
    CourseTabList,
)  # lint-amnesty, pylint: disable=wrong-import-order

from ..utils import (
    ancestor_has_staff_lock,
    find_release_date_source,
    find_staff_lock_source,
    get_split_group_display_name,
    get_user_partition_info,
    get_visibility_partition_info,
    has_children_visible_to_specific_partition_groups,
    is_currently_visible_to_students,
    is_self_paced,
)

from ..helpers import (
    get_parent_xblock,
    import_staged_content_from_user_clipboard,
    is_unit,
    xblock_primary_child_category,
    xblock_studio_url,
    xblock_type_display_name,
)


from .helpers import (
    _create_block,
    _delete_item,
    _is_library_component_limit_reached,
    get_xblock,
    _get_source_index,
    validate_and_update_xblock_due_date,
    _update_with_callback,
    _duplicate_block,
    DIRECT_ONLY_CATEGORIES,
)
from .get_block_info import get_block_info
from .create_xblock_info import _create_xblock_ancestor_info
from .usage_key_with_run import usage_key_with_run


def is_source_item_in_target_parents(source_item, target_parent):
    """
    Returns True if source item is found in target parents otherwise False.

    Arguments:
        source_item (XBlock): Source Xblock.
        target_parent (XBlock): Target XBlock.
    """
    target_ancestors = _create_xblock_ancestor_info(target_parent, is_concise=True)[
        "ancestors"
    ]
    for target_ancestor in target_ancestors:
        if str(source_item.location) == target_ancestor["id"]:
            return True
    return False


def _move_item(source_usage_key, target_parent_usage_key, user, target_index=None):
    """
    Move an existing xblock as a child of the supplied target_parent_usage_key.

    Arguments:
        source_usage_key (BlockUsageLocator): Locator of source item.
        target_parent_usage_key (BlockUsageLocator): Locator of target parent.
        target_index (int): If provided, insert source item at provided index location in target_parent_usage_key item.

    Returns:
        JsonResponse: Information regarding move operation. It may contains error info if an invalid move operation
            is performed.
    """
    # Get the list of all parentable component type XBlocks.
    parent_component_types = list(
        {
            name
            for name, class_ in XBlock.load_classes()
            if getattr(class_, "has_children", False)
        }
        - set(DIRECT_ONLY_CATEGORIES)
    )

    store = modulestore()
    with store.bulk_operations(source_usage_key.course_key):
        source_item = store.get_item(source_usage_key)
        source_parent = source_item.get_parent()
        target_parent = store.get_item(target_parent_usage_key)
        source_type = source_item.category
        target_parent_type = target_parent.category
        error = None

        # Store actual/initial index of the source item. This would be sent back with response,
        # so that with Undo operation, it would easier to move back item to it's original/old index.
        source_index = _get_source_index(source_usage_key, source_parent)

        valid_move_type = {
            "sequential": "vertical",
            "chapter": "sequential",
        }

        if (
            valid_move_type.get(target_parent_type, "") != source_type
            and target_parent_type not in parent_component_types
        ):
            error = _(
                "You can not move {source_type} into {target_parent_type}."
            ).format(
                source_type=source_type,
                target_parent_type=target_parent_type,
            )
        elif (
            source_parent.location == target_parent.location
            or source_item.location in target_parent.children
        ):
            error = _("Item is already present in target location.")
        elif source_item.location == target_parent.location:
            error = _("You can not move an item into itself.")
        elif is_source_item_in_target_parents(source_item, target_parent):
            error = _("You can not move an item into it's child.")
        elif target_parent_type == "split_test":
            error = _("You can not move an item directly into content experiment.")
        elif source_index is None:
            error = _("{source_usage_key} not found in {parent_usage_key}.").format(
                source_usage_key=str(source_usage_key),
                parent_usage_key=str(source_parent.location),
            )
        else:
            try:
                target_index = int(target_index) if target_index is not None else None
                if (
                    target_index is not None
                    and len(target_parent.children) < target_index
                ):
                    error = _(
                        "You can not move {source_usage_key} at an invalid index ({target_index})."
                    ).format(
                        source_usage_key=str(source_usage_key),
                        target_index=target_index,
                    )
            except ValueError:
                error = _(
                    "You must provide target_index ({target_index}) as an integer."
                ).format(target_index=target_index)
        if error:
            return JsonResponse({"error": error}, status=400)

        # When target_index is provided, insert xblock at target_index position, otherwise insert at the end.
        insert_at = (
            target_index if target_index is not None else len(target_parent.children)
        )

        store.update_item_parent(
            item_location=source_item.location,
            new_parent_location=target_parent.location,
            old_parent_location=source_parent.location,
            insert_at=insert_at,
            user_id=user.id,
        )

        log.info(
            "MOVE: %s moved from %s to %s at %d index",
            str(source_usage_key),
            str(source_parent.location),
            str(target_parent_usage_key),
            insert_at,
        )

        context = {
            "move_source_locator": str(source_usage_key),
            "parent_locator": str(target_parent_usage_key),
            "source_index": target_index if target_index is not None else source_index,
        }
        return JsonResponse(context)


def modify_xblock(usage_key, request):
    request_data = request.json
    return _save_xblock(
        request.user,
        get_xblock(usage_key, request.user),
        data=request_data.get("data"),
        children_strings=request_data.get("children"),
        metadata=request_data.get("metadata"),
        nullout=request_data.get("nullout"),
        grader_type=request_data.get("graderType"),
        is_prereq=request_data.get("isPrereq"),
        prereq_usage_key=request_data.get("prereqUsageKey"),
        prereq_min_score=request_data.get("prereqMinScore"),
        prereq_min_completion=request_data.get("prereqMinCompletion"),
        publish=request_data.get("publish"),
        fields=request_data.get("fields"),
    )



def _save_xblock(  # lint-amnesty, pylint: disable=too-many-statements
    user,
    xblock,
    data=None,
    children_strings=None,
    metadata=None,
    nullout=None,
    grader_type=None,
    is_prereq=None,
    prereq_usage_key=None,
    prereq_min_score=None,
    prereq_min_completion=None,
    publish=None,
    fields=None,
):
    """
    Saves xblock w/ its fields. Has special processing for grader_type, publish, and nullout and Nones in metadata.
    nullout means to truly set the field to None whereas nones in metadata mean to unset them (so they revert
    to default).

    """
    store = modulestore()
    # Perform all xblock changes within a (single-versioned) transaction
    with store.bulk_operations(xblock.location.course_key):
        # Don't allow updating an xblock and discarding changes in a single operation (unsupported by UI).
        if publish == "discard_changes":
            store.revert_to_published(xblock.location, user.id)
            # Returning the same sort of result that we do for other save operations. In the future,
            # we may want to return the full XBlockInfo.
            return JsonResponse({"id": str(xblock.location)})

        old_metadata = own_metadata(xblock)
        old_content = xblock.get_explicitly_set_fields_by_scope(Scope.content)

        if data:
            # TODO Allow any scope.content fields not just "data" (exactly like the get below this)
            xblock.data = data
        else:
            data = old_content["data"] if "data" in old_content else None

        if fields:
            for field_name in fields:
                setattr(xblock, field_name, fields[field_name])

        if children_strings is not None:
            children = []
            for child_string in children_strings:
                children.append(usage_key_with_run(child_string))

            # if new children have been added, remove them from their old parents
            new_children = set(children) - set(xblock.children)
            for new_child in new_children:
                old_parent_location = store.get_parent_location(new_child)
                if old_parent_location:
                    old_parent = store.get_item(old_parent_location)
                    old_parent.children.remove(new_child)
                    old_parent = _update_with_callback(old_parent, user)
                else:
                    # the Studio UI currently doesn't present orphaned children, so assume this is an error
                    return JsonResponse(
                        {
                            "error": "Invalid data, possibly caused by concurrent authors."
                        },
                        400,
                    )

            # make sure there are no old children that became orphans
            # In a single-author (no-conflict) scenario, all children in the persisted list on the server should be
            # present in the updated list.  If there are any children that have been dropped as part of this update,
            # then that would be an error.
            #
            # We can be even more restrictive in a multi-author (conflict), by returning an error whenever
            # len(old_children) > 0. However, that conflict can still be "merged" if the dropped child had been
            # re-parented. Hence, the check for the parent in the any statement below.
            #
            # Note that this multi-author conflict error should not occur in modulestores (such as Split) that support
            # atomic write transactions.  In Split, if there was another author who moved one of the "old_children"
            # into another parent, then that child would have been deleted from this parent on the server. However,
            # this is error could occur in modulestores (such as Draft) that do not support atomic write-transactions
            old_children = set(xblock.children) - set(children)
            if any(
                store.get_parent_location(old_child) == xblock.location
                for old_child in old_children
            ):
                # since children are moved as part of a single transaction, orphans should not be created
                return JsonResponse(
                    {"error": "Invalid data, possibly caused by concurrent authors."},
                    400,
                )

            # set the children on the xblock
            xblock.children = children

        # also commit any metadata which might have been passed along
        if nullout is not None or metadata is not None:
            # the postback is not the complete metadata, as there's system metadata which is
            # not presented to the end-user for editing. So let's use the original (existing_item) and
            # 'apply' the submitted metadata, so we don't end up deleting system metadata.
            if nullout is not None:
                for metadata_key in nullout:
                    setattr(xblock, metadata_key, None)

            # update existing metadata with submitted metadata (which can be partial)
            # IMPORTANT NOTE: if the client passed 'null' (None) for a piece of metadata that means 'remove it'. If
            # the intent is to make it None, use the nullout field
            if metadata is not None:
                for metadata_key, value in metadata.items():
                    field = xblock.fields[metadata_key]

                    if value is None:
                        field.delete_from(xblock)
                    else:
                        try:
                            value = field.from_json(value)
                        except ValueError as verr:
                            reason = _("Invalid data")
                            if str(verr):
                                reason = _("Invalid data ({details})").format(
                                    details=str(verr)
                                )
                            return JsonResponse({"error": reason}, 400)

                        field.write_to(xblock, value)

        validate_and_update_xblock_due_date(xblock)
        # update the xblock and call any xblock callbacks
        xblock = _update_with_callback(xblock, user, old_metadata, old_content)

        # for static tabs, their containing course also records their display name
        course = store.get_course(xblock.location.course_key)
        if xblock.location.block_type == "static_tab":
            # find the course's reference to this tab and update the name.
            static_tab = CourseTabList.get_tab_by_slug(
                course.tabs, xblock.location.name
            )
            # only update if changed
            if static_tab:
                update_tab = False
                if static_tab["name"] != xblock.display_name:
                    static_tab["name"] = xblock.display_name
                    update_tab = True
                if static_tab["course_staff_only"] != xblock.course_staff_only:
                    static_tab["course_staff_only"] = xblock.course_staff_only
                    update_tab = True
                if update_tab:
                    store.update_item(course, user.id)

        result = {
            "id": str(xblock.location),
            "data": data,
            "metadata": own_metadata(xblock),
        }

        if grader_type is not None:
            result.update(
                CourseGradingModel.update_section_grader_type(xblock, grader_type, user)
            )

        # Save gating info
        if xblock.category == "sequential" and course.enable_subsection_gating:
            if is_prereq is not None:
                if is_prereq:
                    gating_api.add_prerequisite(
                        xblock.location.course_key, xblock.location
                    )
                else:
                    gating_api.remove_prerequisite(xblock.location)
                result["is_prereq"] = is_prereq

            if prereq_usage_key is not None:
                gating_api.set_required_content(
                    xblock.location.course_key,
                    xblock.location,
                    prereq_usage_key,
                    prereq_min_score,
                    prereq_min_completion,
                )

        # If publish is set to 'republish' and this item is not in direct only categories and has previously been
        # published, then this item should be republished. This is used by staff locking to ensure that changing the
        # draft value of the staff lock will also update the published version, but only at the unit level.
        if publish == "republish" and xblock.category not in DIRECT_ONLY_CATEGORIES:
            if modulestore().has_published_version(xblock):
                publish = "make_public"

        # Make public after updating the xblock, in case the caller asked for both an update and a publish.
        # Used by Bok Choy tests and by republishing of staff locks.
        if publish == "make_public":
            modulestore().publish(xblock.location, user.id)

        # Note that children aren't being returned until we have a use case.
        return JsonResponse(result, encoder=EdxJSONEncoder)


def handle_xblock(request, usage_key_string=None):
    """
    Service method with business logic for handling xblock requests.
    """
    if usage_key_string:
        usage_key = usage_key_with_run(usage_key_string)

        access_check = (
            has_studio_read_access
            if request.method == "GET"
            else has_studio_write_access
        )
        if not access_check(request.user, usage_key.course_key):
            raise PermissionDenied()

        if request.method == "GET":
            accept_header = request.META.get("HTTP_ACCEPT", "application/json")

            if "application/json" in accept_header:
                fields = request.GET.get("fields", "").split(",")
                if "graderType" in fields:
                    # right now can't combine output of this w/ output of get_block_info, but worthy goal
                    return JsonResponse(
                        CourseGradingModel.get_section_grader_type(usage_key)
                    )
                elif "ancestorInfo" in fields:
                    xblock = get_xblock(usage_key, request.user)
                    ancestor_info = _create_xblock_ancestor_info(
                        xblock, is_concise=True
                    )
                    return JsonResponse(ancestor_info)
                # TODO: pass fields to get_block_info and only return those
                with modulestore().bulk_operations(usage_key.course_key):
                    response = get_block_info(get_xblock(usage_key, request.user))
                return JsonResponse(response)
            else:
                return HttpResponse(status=406)

        elif request.method == "DELETE":
            _delete_item(usage_key, request.user)
            return JsonResponse()
        else:  # Since we have a usage_key, we are updating an existing xblock.
            return modify_xblock(usage_key, request)

    elif request.method in ("PUT", "POST"):
        if "duplicate_source_locator" in request.json:
            parent_usage_key = usage_key_with_run(request.json["parent_locator"])
            duplicate_source_usage_key = usage_key_with_run(
                request.json["duplicate_source_locator"]
            )

            source_course = duplicate_source_usage_key.course_key
            dest_course = parent_usage_key.course_key
            if not has_studio_write_access(
                request.user, dest_course
            ) or not has_studio_read_access(request.user, source_course):
                raise PermissionDenied()

            # Libraries have a maximum component limit enforced on them
            if isinstance(
                parent_usage_key, LibraryUsageLocator
            ) and _is_library_component_limit_reached(parent_usage_key):
                return JsonResponse(
                    {
                        "error": _(
                            "Libraries cannot have more than {limit} components"
                        ).format(limit=settings.MAX_BLOCKS_PER_CONTENT_LIBRARY)
                    },
                    status=400,
                )

            dest_usage_key = _duplicate_block(
                parent_usage_key,
                duplicate_source_usage_key,
                request.user,
                request.json.get("display_name"),
            )
            return JsonResponse(
                {
                    "locator": str(dest_usage_key),
                    "courseKey": str(dest_usage_key.course_key),
                }
            )
        else:
            return _create_block(request)
    elif request.method == "PATCH":
        if "move_source_locator" in request.json:
            move_source_usage_key = usage_key_with_run(
                request.json.get("move_source_locator")
            )
            target_parent_usage_key = usage_key_with_run(
                request.json.get("parent_locator")
            )
            target_index = request.json.get("target_index")
            if not has_studio_write_access(
                request.user, target_parent_usage_key.course_key
            ) or not has_studio_read_access(
                request.user, target_parent_usage_key.course_key
            ):
                raise PermissionDenied()
            return _move_item(
                move_source_usage_key,
                target_parent_usage_key,
                request.user,
                target_index,
            )

        return JsonResponse(
            {"error": "Patch request did not recognise any parameters to handle."},
            status=400,
        )
    else:
        return HttpResponseBadRequest(
            "Only instance creation is supported without a usage key.",
            content_type="text/plain",
        )
