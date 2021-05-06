"""
A common module for managing exceptions. Helps to avoid circular references
"""
from .errors import ERROR_WHILE_READING, FAILED_TO_IMPORT_MODULE


class CourseImportException(Exception):
    """Base exception class for course import workflows."""

    def __init__(self):
        super().__init__(self.description)  # pylint: disable=no-member


class ErrorReadingFileException(CourseImportException):
    """
    Raised when error occurs while trying to read a file.
    """

    def __init__(self, filename, **kwargs):
        self.description = ERROR_WHILE_READING.format(filename)
        super().__init__(**kwargs)


class ModuleFailedToImport(CourseImportException):
    """
    Raised when a module is failed to import.
    """

    def __init__(self, display_name, location, **kwargs):
        self.description = FAILED_TO_IMPORT_MODULE.format(display_name, location)
        super().__init__(**kwargs)


class AssetNotFoundException(Exception):
    """
    Raised when asset not found
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass


class AssetSizeTooLargeException(Exception):
    """
    Raised when the size of an uploaded asset exceeds the maximum size limit.
    """
    pass  # lint-amnesty, pylint: disable=unnecessary-pass
