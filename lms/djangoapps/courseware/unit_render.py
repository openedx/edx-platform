"""
API to render all of the XBlocks in a given unit
"""
import json
import logging
import time

from django.urls import reverse
from opaque_keys.edx.keys import UsageKey
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from xblock.core import XBlock2

from lms.djangoapps.course_blocks.api import get_course_blocks
from lms.djangoapps.courseware.models import StudentModule
from openedx.core.lib.api.view_utils import view_auth_classes
from common.djangoapps.util.json_request import JsonResponse
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.util.keys import BlockKey

log = logging.getLogger(__name__)


@api_view(['GET'])
@view_auth_classes(is_authenticated=True)
def get_unit_blocks(request, usage_id):
    """
    Get (as JSON) the data required to render all of the XBlocks [that the
    current user can see] in the given unit.

    Note: a unit is implemented as a "vertical" XBlock with children, but part
    of the goal of this API is to abstract that away, as part of our long-term
    goal of separating the course outline tree from XBlocks (components/leaves).
    """
    start_time = time.time()
    unit_usage_key = UsageKey.from_string(usage_id)
    course_key = unit_usage_key.context_key

    if unit_usage_key.block_type not in ("vertical", "unit"):
        raise ValidationError({"usage_id": "Not a unit"})
    if not course_key.is_course:
        raise ValidationError({"usage_id": "Not from a course. This API only works with XBlocks in modulestore."})

    store = modulestore()._get_modulestore_for_courselike(course_key)
    with store.bulk_operations(course_key):
        # Bypass normal modulestore functionality so we can load the list of XBlocks in this unit without loading
        # The actual blocks, runtime, etc.
        structure_data = store._lookup_course(course_key.for_branch(ModuleStoreEnum.BranchName.published))

        blocks_data = get_course_blocks(request.user, unit_usage_key)
        # Get the usage keys of all the XBlocks in this unit:
        unit_block_ids = blocks_data.get_children(unit_usage_key)

        student_modules = StudentModule.objects.filter(
            student_id=request.user.id,
            course_id=course_key,
            module_state_key__in=[str(key) for key in unit_block_ids],
        )

        blocks = []
        for usage_key in unit_block_ids:
            block_data_out = {
                "id": str(usage_key),
                "block_type": usage_key.block_type,
            }
            try:
                block_class = XBlock2.load_class(usage_key.block_type, fallback_to_v1=True)
                if issubclass(block_class, XBlock2):
                    block_data_out["xblock_api_version"] = 2
                    block_data_out["content_fields"] = {}
                    block_data_out["system_fields"] = {}
                    block_data_out["user_fields"] = {}

                    def add_field(field_name, value):
                        field = block_class.fields.get(field_name)
                        if field:  # TODO: and not field.private
                            block_data_out["content_fields"][field_name] = field.to_json(value)
                        else:
                            for mixin in store.xblock_mixins:
                                field = mixin.fields.get(field_name)
                                if field:
                                    block_data_out["system_fields"][field_name] = field.to_json(value)
                                    return

                    # We cannot get ALL of the field data from the block transfomers API(s), because they only support a
                    # small subset of fields defined in course_api.blocks.serializers.SUPPORTED_FIELDS. However, all the
                    # "complex" fields where we need to worry about inheritance etc. are in the block transformers API
                    for field_name, value in blocks_data[usage_key].fields.items():
                        add_field(field_name, value)
                        # Note: "fields" like "has_score", "course_version", "completion_mode", "subtree_edited_on"
                        # and "category" will be silently dropped here since they're in the block transformer data but
                        # they aren't actual XBlock fields. (Except lti_block.has_score which is actually a field.)

                    # TODO: load additional fields from split modulestore if needed.
                    block_data = store._get_block_from_structure(
                        structure_data.structure,
                        BlockKey.from_usage_key(usage_key),
                    )
                    definition = store.get_definition(course_key, block_data.definition)
                    for field_name, value in definition["fields"].items():
                        add_field(field_name, value)  # TODO: maybe this is already JSON-compatible? don't need to_json?

                    # Get the user-specific field data:
                    sm = next((sm for sm in student_modules if sm.module_state_key == usage_key), None)
                    if sm:
                        for field_name, value in json.loads(sm.state).items():
                            field = block_class.fields.get(field_name)
                            if field:  # TODO: and not field.private
                                block_data_out["user_fields"][field_name] = value  # value is already in JSON format
                else:
                    block_data_out["xblock_api_version"] = 1
                    block_data_out["embed_uri"] = request.build_absolute_uri(
                        reverse("render_xblock", kwargs={"usage_key_string": str(usage_key)})
                    )
            except Exception as err:
                log.exception(f"Unable to load field data for {usage_key}")
                block_data_out["error"] = type(err).__name__
            finally:
                blocks.append(block_data_out)

    end_time = time.time()
    print(f"✅ rendering the unit took {(end_time - start_time)*1000:.0f}ms on the backend.")

    return JsonResponse({
        "unit": {
            "display_name": blocks_data[unit_usage_key].fields.get("display_name")
        },
        "blocks": blocks,
    })
