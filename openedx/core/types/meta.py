"""
Typing utilities for use on other typing utilities.
"""
from __future__ import annotations

import typing as t


def type_annotation_only(cls: type) -> type:
    """
    Decorates class which should only be used in type annotations.

    This is useful when you want to enhance an existing 3rd-party concrete class with
    type annotations for its members, but don't want the enhanced class to ever actually
    be instantiated. For examples, see openedx.core.types.http.
    """
    if t.TYPE_CHECKING:
        return cls
    return _forbid_init(cls)


def _forbid_init(forbidden: type) -> type:
    """
    Return a class which refuses to be instantiated.
    """
    class _ForbidInit:
        """
        The resulting class.
        """
        def __init__(self, *args, **kwargs):
            raise NotImplementedError(
                f"Class {forbidden.__module__}:{forbidden.__name__} "
                "cannot be instantiated. You may use it as a type annotation, but objects "
                "can only be created from its concrete superclasses."
            )

    return _ForbidInit
