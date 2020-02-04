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


class TeamMembershipImportManager(object):
    """ Stub for https://github.com/edx/edx-platform/pull/22949/files """

    def __init__(self, course_id):
        self.validation_errors = []
        self.import_succeeded = False
        self.number_of_records_added = 0

    def set_team_membership_from_csv(self, file):
        import random

        case = random.randint(0, 2)

        if case == 0:
            self.number_of_records_added = 5
            self.import_succeeded = True
            return True
        elif case == 1:
            self.validation_errors.append('Something bad happened')
        else:
            self.validation_errors.append('Something bad happened')
            self.validation_errors.append('Something else bad happened')

        self.import_succeeded = False
        return False
