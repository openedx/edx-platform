"""
Utilities for warning about deprecated imports supported by the sys_path_hack/ system.

See /docs/decisions/0007-sys-path-modification-removal.rst for details.
"""

import warnings


class SysPathHackWarning(DeprecationWarning):
    """
    A warning that a module is being imported from its old, non-prefixed location.

    edx-platform modules should be imported from the root of the repository.
    For example, `from lms.djangoapps.course_wiki import views` is good.

    However, we historically modify `sys.path` to allow importing relative to
    certain subdirectories. For example, `from course_wiki ipmort views` currently
    works.

    We want to stardize on the prefixed version for a few different reasons.
    """

    def __init__(self, import_prefix, unprefixed_import_path):
        super().__init__()
        self.import_prefix = import_prefix
        self.unprefixed_import_path = unprefixed_import_path
        self.desired_import_path = import_prefix + "." + unprefixed_import_path

    def __str__(self):
        return (
            "Importing {self.unprefixed_import_path} instead of "
            "{self.desired_import_path} is deprecated"
        ).format(self=self)


def warn_deprecated_import(import_prefix, unprefixed_import_path):
    """
    Warn that a module is being imported from its old, non-prefixed location.
    """
    warnings.warn(
        SysPathHackWarning(import_prefix, unprefixed_import_path),
        stacklevel=3,  # Should surface the line that is doing the importing.
    )
