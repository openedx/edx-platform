"""
    Service with business logic supporting a view in handling an incoming xblock request.
    This method is used both by the internal xblock_handler API and by
    the public studio content API. The method handles GET, POST, PUT, PATCH, and DELETE requests.
"""

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.translation import gettext as _
from opaque_keys.edx.locator import LibraryUsageLocator

from cms.djangoapps.models.settings.course_grading import CourseGradingModel
from common.djangoapps.student.auth import (
    has_studio_read_access,
    has_studio_write_access,
)
from common.djangoapps.util.json_request import JsonResponse
from xmodule.modulestore.django import (
    modulestore,
)  # lint-amnesty, pylint: disable=wrong-import-order

from .usage_key_with_run import usage_key_with_run
from .helpers import (
    _create_block,
    _create_xblock_ancestor_info,
    _delete_item,
    _duplicate_block,
    _is_library_component_limit_reached,
    _move_item,
    get_xblock,
    get_block_info,
    modify_xblock
)

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
