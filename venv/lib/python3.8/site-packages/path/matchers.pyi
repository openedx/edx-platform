from __future__ import annotations

from typing import Any, Callable, overload

from typing_extensions import Literal

from path import Path
@overload
def load(param: None) -> Null: ...
@overload
def load(param: str) -> Pattern: ...
@overload
def load(param: Any) -> Any: ...

class Base:
    pass

class Null(Base):
    def __call__(self, path: str) -> Literal[True]: ...

class Pattern(Base):
    def __init__(self, pattern: str) -> None: ...
    def get_pattern(self, normcase: Callable[[str], str]) -> str: ...
    def __call__(self, path: Path) -> bool: ...

class CaseInsensitive(Pattern):
    normcase: Callable[[str], str]
