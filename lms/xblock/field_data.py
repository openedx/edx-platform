"""
:class:`~xblock.field_data.FieldData` subclasses used by the LMS
"""

from xblock.field_data import ReadOnlyFieldData, SplitFieldData
from xblock.fields import Scope


def lms_field_data(authored_data, student_data):
    """
    Returns a new :class:`~xblock.field_data.FieldData` that
    reads all UserScope.ONE and UserScope.ALL fields from `student_data`
    and all UserScope.NONE fields from `authored_data`. It also prevents
    writing to `authored_data`.
    """
    authored_data = ReadOnlyFieldData(authored_data)
    return SplitFieldData({
        Scope.content: authored_data,
        Scope.settings: authored_data,
        Scope.parent: authored_data,
        Scope.children: authored_data,
        Scope.user_state_summary: student_data,
        Scope.user_state: student_data,
        Scope.user_info: student_data,
        Scope.preferences: student_data,
    })
