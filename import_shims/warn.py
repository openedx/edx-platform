"""
Utilities for warning about deprecated imports temporarily supported by
the import_shim/ system.

See /docs/decisions/0007-sys-path-modification-removal.rst for details.
"""

import warnings

from django.conf import settings
from edx_django_utils.monitoring import set_custom_attribute


class DeprecatedEdxPlatformImportWarning(DeprecationWarning):
    """
    A warning that a module is being imported from an unsupported location.

    Example use case:
        edx-platform modules should be imported from the root of the repository.

        For example, `from lms.djangoapps.course_wiki import views` is good.

        However, we historically modify `sys.path` to allow importing relative to
        certain subdirectories. For example, `from course_wiki ipmort views` currently
        works.

        We want to stardize on the prefixed version for a few different reasons.
    """

    def __init__(self, old_import, new_import):
        super().__init__()
        self.old_import = old_import
        self.new_import = new_import

    def __str__(self):
        return (
            "Importing {self.old_import} instead of {self.new_import} is deprecated"
        ).format(self=self)


class DeprecatedEdxPlatformImportError(Exception):
    """
    Error: An edx-platform module is being imported from an unsupported location.

    See `DeprecatedEdxPlatformImportWarning` above for context.
    """

    def __init__(self, old_import, new_import):
        super().__init__()
        self.old_import = old_import
        self.new_import = new_import

    def __str__(self):
        return (
            "Importing {self.old_import} instead of {self.new_import} is deprecated"
        ).format(self=self)


def warn_deprecated_import(old_import, new_import):
    """
    Warn that a module is being imported from its old location.
    """
    if settings.ERROR_ON_DEPRECATED_EDX_PLATFORM_IMPORTS:
        raise DeprecatedEdxPlatformImportError(old_import, new_import)
    set_custom_attribute("deprecated_edx_platform_import", old_import)
    warnings.warn(
        DeprecatedEdxPlatformImportWarning(old_import, new_import),
        stacklevel=3,  # Should surface the line that is doing the importing.
    )
