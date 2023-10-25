"""
Types used by content tagging API and implementation
"""
from typing import Union

from opaque_keys.edx.keys import LearningContextKey, UsageKey

ContentKey = Union[LearningContextKey, UsageKey]
