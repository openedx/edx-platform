"""
Exceptions related to safe exec.
"""


class CodejailServiceParseError(Exception):
    """
    An exception that is raised whenever we have issues with data parsing.
    """


class CodejailServiceStatusError(Exception):
    """
    An exception that is raised whenever Codejail service response status is different to 200.
    """


class CodejailServiceUnavailable(Exception):
    """
    An exception that is raised whenever Codejail service is unavailable.
    """
