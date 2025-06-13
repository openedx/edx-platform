"""
Value objects
"""
from __future__ import annotations

from enum import Enum

from openedx.core.djangoapps.content_libraries.api import ContainerType


class CompositionLevel(Enum):
    """
    Enumeration of composition levels for legacy content.

    Defined in increasing order of complexity so that `is_higher_than` works correctly.
    """
    # Components are individual XBlocks, e.g. Problem
    Component = 'component'

    # Container types currently supported by Content Libraries
    Unit = ContainerType.Unit.value
    Subsection = ContainerType.Subsection.value
    Section = ContainerType.Section.value
    OutlineRoot = ContainerType.OutlineRoot.value

    @property
    def is_container(self) -> bool:
        return self is not self.Component

    def is_higher_than(self, other: 'CompositionLevel') -> bool:
        """
        Is this composition level 'above' (more complex than) the other?
        """
        levels: list[CompositionLevel] = list(self.__class__)
        return levels.index(self) > levels.index(other)

    @classmethod
    def supported_choices(cls) -> list[tuple[str, str]]:
        """
        Returns all supported composition levels as a list of tuples,
        for use in a Django Models ChoiceField.
        """
        return [
            (composition_level.value, composition_level.name)
            for composition_level in cls
        ]
