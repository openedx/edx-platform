""" API Views for unit page """

import logging
import edx_api_doc_tools as apidocs
from django.http import HttpResponseBadRequest
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from cms.djangoapps.contentstore.utils import (
    get_container_handler_context,
    get_user_partition_info,
    get_visibility_partition_info,
    get_xblock_validation_messages,
    get_xblock_render_error,
)
from cms.djangoapps.contentstore.views.component import _get_item_in_course
from cms.djangoapps.contentstore.xblock_storage_handlers.view_handlers import get_xblock
from cms.djangoapps.contentstore.rest_api.v1.serializers import (
    ContainerHandlerSerializer,
    VerticalContainerSerializer,
)
from cms.lib.xblock.upstream_sync import UpstreamLink
from openedx.core.lib.api.view_utils import view_auth_classes
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.exceptions import ItemNotFoundError  # lint-amnesty, pylint: disable=wrong-import-order

from cms.djangoapps.contentstore.rest_api.v1.mixins import ContainerHandlerMixin


log = logging.getLogger(__name__)


@view_auth_classes(is_authenticated=True)
class ContainerHandlerView(APIView, ContainerHandlerMixin):
    """
    View for container xblock requests to get vertical data.
    """

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                "usage_key_string",
                apidocs.ParameterLocation.PATH,
                description="Container usage key",
            ),
        ],
        responses={
            200: ContainerHandlerSerializer,
            401: "The requester is not authenticated.",
            404: "The requested locator does not exist.",
        },
    )
    def get(self, request: Request, usage_key_string: str):
        """
        Get an object containing vertical data.

        **Example Request**

            GET /api/contentstore/v1/container_handler/{usage_key_string}

        **Response Values**

        If the request is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response contains a single dict that contains keys that
        are the vertical's container data.

        **Example Response**

        ```json
        {
            "language_code": "zh-cn",
            "action": "view",
            "xblock": {
                "display_name": "Labs and Demos",
                "display_type": "单元",
                "category": "vertical"
            },
            "is_unit_page": true,
            "is_collapsible": false,
            "position": 1,
            "prev_url": "block-v1-edX%2BDemo_Course%2Btype%40vertical%2Bblock%404e592689563243c484",
            "next_url": "block-v1%3AedX%2BDemoX%2BDemo_Course%2Btype%40vertical%2Bblock%40vertical_aae927868e55",
            "new_unit_category": "vertical",
            "outline_url": "/course/course-v1:edX+DemoX+Demo_Course?format=concise",
            "ancestor_xblocks": [
                {
                "children": [
                    {
                    "url": "/course/course-v1:edX+DemoX+Demo_Course?show=block-v1%3AedX%2BDemoX%2BDemo_Course%2Btype%",
                    "display_name": "Introduction"
                    },
                    ...
                ],
                "title": "Example Week 2: Get Interactive",
                "is_last": false
                },
                ...
            ],
            "component_templates": [
                {
                "type": "advanced",
                "templates": [
                    {
                    "display_name": "批注",
                    "category": "annotatable",
                    "boilerplate_name": null,
                    "hinted": false,
                    "tab": "common",
                    "support_level": true
                    },
                    ...
                },
                ...
            ],
            "xblock_info": {},
            "draft_preview_link": "//preview.localhost:18000/courses/course-v1:edX+DemoX+Demo_Course/...",
            "published_preview_link": "///courses/course-v1:edX+DemoX+Demo_Course/jump_to/...",
            "show_unit_tags": false,
            "user_clipboard": {
                "content": null,
                "source_usage_key": "",
                "source_context_title": "",
                "source_edit_url": ""
            },
            "is_fullwidth_content": false,
            "assets_url": "/assets/course-v1:edX+DemoX+Demo_Course/",
            "unit_block_id": "d6cee45205a449369d7ef8f159b22bdf",
            "subsection_location": "block-v1:edX+DemoX+Demo_Course+type@sequential+block@graded_simulations"
            "course_sequence_ids": [
                "block-v1:edX+DemoX+Demo_Course+type@sequential+block@graded_simulations",
                "block-v1:edX+DemoX+Demo_Course+type@sequential+block@something_else",
                ...
            ],
        }
        ```
        """
        usage_key = self.get_object(usage_key_string)
        course_key = usage_key.course_key
        with modulestore().bulk_operations(course_key):
            try:
                course, xblock, lms_link, preview_lms_link = _get_item_in_course(request, usage_key)
            except ItemNotFoundError:
                return HttpResponseBadRequest()

            context = get_container_handler_context(request, usage_key, course, xblock)
            context.update({
                'draft_preview_link': preview_lms_link,
                'published_preview_link': lms_link,
            })
            serializer = ContainerHandlerSerializer(context)
            return Response(serializer.data)


@view_auth_classes(is_authenticated=True)
class VerticalContainerView(APIView, ContainerHandlerMixin):
    """
    View for container xblock requests to get vertical state and children data.
    """

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                "usage_key_string",
                apidocs.ParameterLocation.PATH,
                description="Vertical usage key",
            ),
        ],
        responses={
            200: VerticalContainerSerializer,
            401: "The requester is not authenticated.",
            404: "The requested locator does not exist.",
        },
    )
    def get(self, request: Request, usage_key_string: str):
        """
        Get an object containing vertical state with children data.

        **Example Request**

            GET /api/contentstore/v1/container/vertical/{usage_key_string}/children

        **Response Values**

        If the request is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response contains a single dict that contains keys that
        are the vertical's container children data.

        **Example Response**

        ```json
        {
            "children": [
                {
                    "name": "Drag and Drop",
                    "block_id": "block-v1:org+101+101+type@drag-and-drop-v2+block@7599275ace6b46f5a482078a2954ca16",
                    "block_type": "drag-and-drop-v2",
                    "user_partition_info": {},
                    "user_partitions": {}
                    "upstream_link": null,
                    "actions": {
                        "can_copy": true,
                        "can_duplicate": true,
                        "can_move": true,
                        "can_manage_access": true,
                        "can_delete": true,
                        "can_manage_tags": true,
                    },
                    "has_validation_error": false,
                    "validation_errors": [],
                },
                {
                    "name": "Video",
                    "block_id": "block-v1:org+101+101+type@video+block@0e3d39b12d7c4345981bda6b3511a9bf",
                    "block_type": "video",
                    "user_partition_info": {},
                    "user_partitions": {}
                    "upstream_link": {
                        "upstream_ref": "lb:org:mylib:video:404",
                        "version_synced": 16
                        "version_available": null,
                        "error_message": "Linked library item not found: lb:org:mylib:video:404",
                        "ready_to_sync": false,
                    },
                    "actions": {
                        "can_copy": true,
                        "can_duplicate": true,
                        "can_move": true,
                        "can_manage_access": true,
                        "can_delete": true,
                        "can_manage_tags": true,
                    }
                    "validation_messages": [],
                    "render_error": "",
                },
                {
                    "name": "Text",
                    "block_id": "block-v1:org+101+101+type@html+block@3e3fa1f88adb4a108cd14e9002143690",
                    "block_type": "html",
                    "user_partition_info": {},
                    "user_partitions": {},
                    "upstream_link": {
                        "upstream_ref": "lb:org:mylib:html:abcd",
                        "version_synced": 43,
                        "version_available": 49,
                        "error_message": null,
                        "ready_to_sync": true,
                    },
                    "actions": {
                        "can_copy": true,
                        "can_duplicate": true,
                        "can_move": true,
                        "can_manage_access": true,
                        "can_delete": true,
                        "can_manage_tags": true,
                    },
                    "validation_messages": [
                        {
                            "text": "This component's access settings contradict its parent's access settings.",
                            "type": "error"
                        }
                    ],
                    "render_error": "Unterminated control keyword: 'if' in file '../problem.html'",
                },
            ],
            "is_published": false,
            "can_paste_component": true,
        }
        ```
        """
        usage_key = self.get_object(usage_key_string)
        current_xblock = get_xblock(usage_key, request.user)
        is_course = current_xblock.scope_ids.usage_id.context_key.is_course

        with modulestore().bulk_operations(usage_key.course_key):
            # load course once to reuse it for user_partitions query
            course = modulestore().get_course(current_xblock.location.course_key)
            children = []
            if hasattr(current_xblock, "children"):
                for child in current_xblock.children:
                    child_info = modulestore().get_item(child)
                    user_partition_info = get_visibility_partition_info(child_info, course=course)
                    user_partitions = get_user_partition_info(child_info, course=course)
                    upstream_link = UpstreamLink.try_get_for_block(child_info)
                    validation_messages = get_xblock_validation_messages(child_info)
                    render_error = get_xblock_render_error(request, child_info)

                    children.append({
                        "xblock": child_info,
                        "name": child_info.display_name_with_default,
                        "block_id": child_info.location,
                        "block_type": child_info.location.block_type,
                        "user_partition_info": user_partition_info,
                        "user_partitions": user_partitions,
                        "upstream_link": (
                            # If the block isn't linked to an upstream (which is by far the most common case) then just
                            # make this field null, which communicates the same info, but with less noise.
                            upstream_link.to_json() if upstream_link.upstream_ref
                            else None
                        ),
                        "validation_messages": validation_messages,
                        "render_error": render_error,
                    })

            is_published = False
            try:
                is_published = not modulestore().has_changes(current_xblock)
            except ItemNotFoundError:
                logging.error('Could not find any changes for block [%s]', usage_key)

            container_data = {
                "children": children,
                "is_published": is_published,
                "can_paste_component": is_course,
            }
            serializer = VerticalContainerSerializer(container_data)
            return Response(serializer.data)
