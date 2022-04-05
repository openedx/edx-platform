"""
Test utilities for waffle utilities.
"""

# Can be used with FilteredQueryCountMixin.assertNumQueries() to ignore
# waffle tables. For example:
#   QUERY_COUNT_TABLE_IGNORELIST = WAFFLE_TABLES
#   with self.assertNumQueries(6, table_ignorelist=QUERY_COUNT_TABLE_IGNORELIST):
WAFFLE_TABLES = [
    "waffle_utils_waffleflagcourseoverridemodel",
    "waffle_utils_waffleflagorgoverridemodel",
    "waffle_flag",
    "waffle_switch",
    "waffle_sample",
]
