"""
This migration enabled Multi-Tenant Emails on Tahoe.

This app exists solely to rollback what the `common/djangoapps/database_fixups` does.
"""

from django.conf import settings
from unittest import SkipTest
