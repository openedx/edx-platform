"""Errors thrown in the Team API"""


class TeamAPIRequestError(Exception):
    """There was a problem with a request to the Team API."""
    pass


class NotEnrolledInCourseForTeam(TeamAPIRequestError):
    """User is not enrolled in the course for the team they are trying to join."""
    pass


class AlreadyOnTeamInCourse(TeamAPIRequestError):
    """User is already a member of another team in the same course."""
    pass
