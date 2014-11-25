"""
List of errors that can be returned by the mobile api
"""


def format_error(error_code, message):
    """
    Converts an error_code and message into a response body
    """
    return {"errors": [{"code": error_code, "message": message}]}

ERROR_INVALID_COURSE_ID = format_error("invalid-course-id", "Could not find course for course_id")
ERROR_INVALID_MODIFICATION_DATE = format_error("invalid-modification-date", "Could not parse modification_date")
ERROR_INVALID_MODULE_ID = format_error("invalid-module-id", "Could not find module for module_id")
ERROR_INVALID_USER_ID = format_error("invalid-user-id", "Could not find user for user_id")
