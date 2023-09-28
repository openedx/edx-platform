"""
:class:`~xblock.field_data.FieldData` subclasses used by the CMS
"""


from xblock.field_data import SplitFieldData
from xblock.fields import Scope


class CmsFieldData(SplitFieldData):
    """
    A :class:`~xblock.field_data.FieldData` that
    reads all UserScope.ONE and UserScope.ALL fields from `student_data`
    and all UserScope.NONE fields from `authored_data`. It allows writing to`authored_data`.
    """
    def __init__(self, authored_data, student_data):
        # Make sure that we don't repeatedly nest CmsFieldData instances
        if isinstance(authored_data, CmsFieldData):
            authored_data = authored_data._authored_data

        self._authored_data = authored_data
        self._student_data = student_data

        super().__init__({
            Scope.content: authored_data,
            Scope.settings: authored_data,
            Scope.parent: authored_data,
            Scope.children: authored_data,
            Scope.user_state_summary: student_data,
            Scope.user_state: student_data,
            Scope.user_info: student_data,
            Scope.preferences: student_data,
        })
