"""
CSV processing and generation utilities for Teams LMS app.
"""


def load_team_membership_csv(course, response):
    """
    Load a CSV detailing course membership.

    Arguments:
        course (CourseDescriptor): Course module for which CSV
            download has been requested.
        response (HttpResponse): Django response object to which
            the CSV content will be written.
    """
    # This function needs to be implemented (TODO MST-31).
    _ = course
    not_implemented_message = (
        "Team membership CSV download is not yet implemented."
    )
    response.write(not_implemented_message + "\n")
