# pylint: disable=unused-import
"""
Python APIs exposed by the bulk_email app to other in-process apps.
"""

# Public Bulk Email Functions
from bulk_email.models_api import (
    is_bulk_email_enabled_for_course,
    is_bulk_email_feature_enabled,
    is_user_opted_out_for_course,
)
