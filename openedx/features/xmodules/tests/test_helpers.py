from datetime import datetime

import pytest

from openedx.features.xmodules.constants import DATE_FORMAT
from openedx.features.xmodules.helpers import get_due_date_for_problem_xblock

current_date = datetime.now()
formatted_current_date = current_date.strftime(DATE_FORMAT)


@pytest.mark.parametrize(
   'due, module_category, expected_result', [
        (current_date, 'audio', None),
        (current_date, 'problem', formatted_current_date),
        (None, 'problem', None)
    ]
)
def test_get_due_date_for_problem_xblock(due, module_category, expected_result):
    assert get_due_date_for_problem_xblock(due, module_category) == expected_result
