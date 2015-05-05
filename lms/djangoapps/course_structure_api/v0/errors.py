""" Errors used by the Course Structure API. """


class CourseNotFoundError(Exception):
    """ The course was not found. """
    pass


class CourseStructureNotAvailableError(Exception):
    """ The course structure still needs to be generated. """
    pass
