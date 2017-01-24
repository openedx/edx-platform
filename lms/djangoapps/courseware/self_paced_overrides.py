"""
Field overrides for self-paced courses. This allows overriding due
dates for each block in the course.
"""

from .field_overrides import FieldOverrideProvider
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration


class SelfPacedDateOverrideProvider(FieldOverrideProvider):
    """
    A concrete implementation of
    :class:`~courseware.field_overrides.FieldOverrideProvider` which allows for
    due dates to be overridden for self-paced courses.
    """
    def get(self, block, name, default):
        # Remove due dates
        if name == 'due':
            return None
        # Remove release dates for course content
        if name == 'start' and block.category != 'course':
            return None

        return default

    @classmethod
    def enabled_for(cls, block):
        """This provider is enabled for self-paced courses only."""
        return block is not None and block.self_paced and SelfPacedConfiguration.current().enabled
