"""
Types used by content tagging API and implementation
"""
from typing import Union

from opaque_keys.edx.keys import CourseKey, UsageKey

ContentKey = Union[CourseKey, UsageKey]
