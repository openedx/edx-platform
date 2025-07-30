# errors.py
"""
Custom error handling for the XQueue submission interface.
"""


class XQueueSubmissionError(Exception):
    """Base class for all XQueue submission errors."""


class JSONParsingError(XQueueSubmissionError):
    """Raised when JSON parsing fails."""
    MESSAGE = "Error parsing {name}: {error}"

    def __init__(self, name, error):
        super().__init__(self.MESSAGE.format(name=name, error=error))


class MissingKeyError(XQueueSubmissionError):
    """Raised when a required key is missing."""
    MESSAGE = "Missing key: {key}"

    def __init__(self, key):
        super().__init__(self.MESSAGE.format(key=key))


class ValidationError(XQueueSubmissionError):
    """Raised when a validation check fails."""
    MESSAGE = "Validation error: {error}"

    def __init__(self, error):
        super().__init__(self.MESSAGE.format(error=error))


class TypeErrorSubmission(XQueueSubmissionError):
    """Raised when an invalid type is encountered."""
    MESSAGE = "Type error: {error}"

    def __init__(self, error):
        super().__init__(self.MESSAGE.format(error=error))


class RuntimeErrorSubmission(XQueueSubmissionError):
    """Raised for runtime errors."""
    MESSAGE = "Runtime error: {error}"

    def __init__(self, error):
        super().__init__(self.MESSAGE.format(error=error))


class GetSubmissionParamsError(XQueueSubmissionError):
    """Raised when there is an issue getting submission parameters."""
    MESSAGE = "Submission parameters error: {error}"

    def __init__(self, error="Block instance is not defined!"):
        super().__init__(self.MESSAGE.format(error=error))
