"""API Views for unit components handler"""

import logging

import edx_api_doc_tools as apidocs
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from opaque_keys.edx.keys import UsageKey
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from cms.djangoapps.contentstore.rest_api.v1.mixins import ContainerHandlerMixin
from cms.djangoapps.contentstore.toggles import enable_unit_expanded_view
from openedx.core.lib.api.view_utils import view_auth_classes
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

log = logging.getLogger(__name__)


@view_auth_classes(is_authenticated=True)
class UnitComponentsView(APIView, ContainerHandlerMixin):
    """
    View to get all components in a unit by usage key.
    """

    @apidocs.schema(
        parameters=[
            apidocs.string_parameter(
                "usage_key_string",
                apidocs.ParameterLocation.PATH,
                description="Unit usage key",
            ),
        ],
        responses={
            200: "List of components in the unit",
            400: "Invalid usage key or unit not found.",
            401: "The requester is not authenticated.",
            404: "The requested unit does not exist.",
        },
    )
    def get(self, request: Request, usage_key_string: str):
        """
        Get all components in a unit.

        **Example Request**

            GET /api/contentstore/v1/unit_handler/{usage_key_string}

        **Response Values**

        If the request is successful, an HTTP 200 "OK" response is returned.

        The HTTP 200 response contains a dict with a list of all components
        in the unit, including their display names, block types, and block IDs.

        **Example Response**

        ```json
        {
            "unit_id": "block-v1:edX+DemoX+Demo_Course+type@vertical+block@vertical_id",
            "display_name": "My Unit",
            "components": [
                {
                    "block_id": "block-v1:edX+DemoX+Demo_Course+type@video+block@video_id",
                    "block_type": "video",
                    "display_name": "Introduction Video"
                },
                {
                    "block_id": "block-v1:edX+DemoX+Demo_Course+type@html+block@html_id",
                    "block_type": "html",
                    "display_name": "Text Content"
                },
                {
                    "block_id": "block-v1:edX+DemoX+Demo_Course+type@problem+block@problem_id",
                    "block_type": "problem",
                    "display_name": "Practice Problem"
                }
            ]
        }
        ```
        """
        try:
            usage_key = UsageKey.from_string(usage_key_string)
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.error(f"Invalid usage key: {usage_key_string}, error: {str(e)}")
            return HttpResponseBadRequest("Invalid usage key format")

        try:
            # Get the unit xblock
            unit_xblock = modulestore().get_item(usage_key)

            # Verify it's a vertical (unit)
            if unit_xblock.category != "vertical":
                return HttpResponseBadRequest(
                    "The provided usage key is not a unit (vertical)"
                )

            if not enable_unit_expanded_view(unit_xblock.location.course_key):
                return HttpResponseForbidden(
                    "Unit expanded view is disabled for this course"
                )

            components = []

            # Get all children (components) of the unit
            if unit_xblock.has_children:
                for child_usage_key in unit_xblock.children:
                    try:
                        child_xblock = modulestore().get_item(child_usage_key)
                        components.append(
                            {
                                "block_id": str(child_xblock.location),
                                "block_type": child_xblock.category,
                                "display_name": child_xblock.display_name_with_default,
                            }
                        )
                    except ItemNotFoundError:
                        log.warning(f"Child block not found: {child_usage_key}")
                        continue

            response_data = {
                "unit_id": str(usage_key),
                "display_name": unit_xblock.display_name_with_default,
                "components": components,
            }

            return Response(response_data)

        except ItemNotFoundError:
            log.error(f"Unit not found: {usage_key_string}")
            return HttpResponseBadRequest("Unit not found")
        except Exception as e:  # pylint: disable=broad-exception-caught
            log.error(f"Error retrieving unit components: {str(e)}")
            return HttpResponseBadRequest(f"Error retrieving unit components: {str(e)}")
