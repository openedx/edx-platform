"""
Field overrides for self-paced courses. This allows overriding due
dates for each block in the course.
"""

from .field_overrides import FieldOverrideProvider


class SelfPacedDateOverrideProvider(FieldOverrideProvider):
    """
    A concrete implementation of
    :class:`~courseware.field_overrides.FieldOverrideProvider` which allows for
    due dates to be overridden for self-paced courses.
    """
    def get(self, block, name, default):
        if name == 'due':
            return None
        return default

    @classmethod
    def enabled_for(cls, course):
        """This provider is enabled for self-paced courses only."""
        return course.self_paced
