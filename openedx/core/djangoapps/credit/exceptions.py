""" This module contains the exceptions raised in credit course requirements """


class InvalidCreditRequirements(Exception):
    """ The exception occurs when the requirement dictionary has invalid format. """
    pass


class InvalidCreditCourse(Exception):
    """ The exception occurs when the the course is not marked as a Credit Course. """
    pass
