"""
Test utilities for waffle utilities.
"""

# Import from edx-toggles to preserve import paths
# pylint: disable=unused-import
from edx_toggles.toggles.testutils import override_waffle_flag

# Can be used with FilteredQueryCountMixin.assertNumQueries() to blacklist
# waffle tables. For example:
#   QUERY_COUNT_TABLE_BLACKLIST = WAFFLE_TABLES
#   with self.assertNumQueries(6, table_blacklist=QUERY_COUNT_TABLE_BLACKLIST):
WAFFLE_TABLES = [
    "waffle_utils_waffleflagcourseoverridemodel",
    "waffle_flag",
    "waffle_switch",
    "waffle_sample",
]
