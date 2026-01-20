"""Utilities for retrieving Open Response Assessments (ORAs) data for instructor dashboards."""

from django.utils.translation import gettext as _
from openassessment.data import OraAggregateData

from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order

DEFAULT_ORA_METRICS = {
    'total': 0,
    'training': 0,
    'peer': 0,
    'self': 0,
    'waiting': 0,
    'staff': 0,
    'final_grade_received': 0,
}


def get_open_response_assessment_list(course):
    """
    Return a list of Open Response Assessments (ORAs) for a course.

    Uses OraAggregateData to collect response metrics, which transparently
    supports both ORA1 and ORA2 data.
    """
    course_key = course.id
    store = modulestore()

    # Collect ORA2 response metrics keyed by block location
    ora2_responses = OraAggregateData.collect_ora2_responses(str(course_key))

    # Fetch all openassessment blocks in the course
    openassessment_blocks = store.get_items(
        course_key,
        qualifiers={'category': 'openassessment'},
    )

    parents_cache = {}
    ora_items = []

    for block in openassessment_blocks:
        block_id = str(block.location)
        parent_id = block.parent

        # Cache parent lookups to avoid repeated modulestore calls
        if parent_id not in parents_cache:
            parents_cache[parent_id] = store.get_item(parent_id)

        parent_block = parents_cache[parent_id]

        assessment_name = (
            _("Team") + " : " + block.display_name
            if block.teams_enabled
            else block.display_name
        )

        ora_assessment_data = {
            'id': block_id,
            'name': assessment_name,
            'parent_name': parent_block.display_name,
            **DEFAULT_ORA_METRICS,
        }

        # Merge collected metrics (if any)
        ora_assessment_data.update(ora2_responses.get(block_id, {}))
        ora_items.append(ora_assessment_data)

    return ora_items
