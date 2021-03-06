"""
Utilities for warning about deprecated imports temporarily supported by
the import_shim/ system.

See /docs/decisions/0007-sys-path-modification-removal.rst for details.
"""


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
    Raise an error that a module is being imported from an unsupported location.

    The function is named "warn_deprecated_import" because importing
    from these locations used to raise warnings instead of errors,
    but updating all references to the old function name did not seem
    worth it, especially since this function will be removed soon after
    the Lilac release is cut.
    """
    raise DeprecatedEdxPlatformImportError(old_import, new_import)
