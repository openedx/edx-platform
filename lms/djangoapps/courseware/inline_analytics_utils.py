"""
Inline Analytics functions
"""

import json
import cgi
from lxml import etree
from collections import namedtuple

from django.conf import settings

from xmodule.capa_module import CapaModule

ValidResponse = namedtuple('ValidResponse', 'correct_response response_type choice_name_list')  # pylint: disable=invalid-name
AnalyticsContextResponse = namedtuple('AnalyticsContextResponse', 'id correct_response response_type message choice_name_list')  # pylint: disable=invalid-name


def get_responses_data(block):
    """
    Gets Capa data for questions; used by the in-line analytics display.

    Currently supported response types for in-line analytics graphics display are:
       - MultipleChoiceResponse
       - ChoiceResponse

    Currently supported question types for in-line analytics textual display are:
       - OptionResponse
       - NumericalResponse
       - StringResponse
       - FormulaResponse

    Problems with randomize are not currently supported for in-line analytics.
    If settings.ANALYTICS_ANSWER_DIST_URL is unset then returns None
    """
    responses_data = []
    valid_group_nodes = []
    valid_types = getattr(settings, 'INLINE_ANALYTICS_SUPPORTED_TYPES', {})

    if not isinstance(block, CapaModule) or not valid_types:
        return responses_data

    responses = block.lcp.responders.values()
    valid_responses = {}
    rerandomize = False
    if block.rerandomize != 'never':
        rerandomize = True

    for response in responses:
        # Build list of group nodes supported by the analytics api
        valid_group_nodes.extend(response.allowed_inputfields)

        # Categorize response type; 'other' if not supported by the analytics api
        response_type = valid_types.get(response.__class__.__name__, 'other')

        # Determine the part id and correct answer
        response_answers = response.get_answers().items()
        if response_answers:
            part_id, correct_response = response_answers[0]

            # Get a list of the choice names in the order displayed to the user.
            # The is necessary since masking may have been used on the name but
            # only on MultipleChoiceResponse type as of writing.
            try:
                choice_name_list = response.unmask_order()
            except AttributeError:
                choice_name_list = []

            valid_responses[part_id] = ValidResponse(correct_response, response_type, choice_name_list)

    if valid_responses:
        # Loop through all the nodes finding the group elements for each response
        # We need to do this to get the responses in the same order as on the page
        for node in block.lcp.tree.iter(tag=etree.Element):
            part_id = node.attrib.get('id', None)
            if part_id and part_id in valid_responses and node.tag in valid_group_nodes:
                # This is a valid question according to the list of valid responses and we have the group node

                if valid_responses[part_id].response_type == 'other':
                    # Response type is not supported by the analytics api
                    responses_data.append(AnalyticsContextResponse(part_id, None, None, "The analytics cannot be displayed for this type of question.", None))
                elif rerandomize:
                    # Response, actually the problem, has rerandomize != 'never'
                    responses_data.append(AnalyticsContextResponse(part_id, valid_responses[part_id].correct_response, valid_responses[part_id].response_type, "The analytics cannot be displayed for this question as it uses randomization.", None))
                else:
                    # Response is supported by the analytics api and rerandomize == 'never'
                    responses_data.append(AnalyticsContextResponse(part_id, valid_responses[part_id].correct_response, valid_responses[part_id].response_type, None, cgi.escape(json.dumps(valid_responses[part_id].choice_name_list), quote=True)))
    return responses_data
