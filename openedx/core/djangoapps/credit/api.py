""" Contains the APIs for course credit requirements """

from .exceptions import InvalidCreditRequirements
from .models import CreditCourse, CreditRequirement


def set_credit_requirements(course_key, requirements):
    """ Add requirements to given course

    Args:
        course_key(CourseKey): The identifier for course
        requirements(list): List of requirements to be added

    Example:
        >>> set_credit_requirements(
                "course-v1-edX-DemoX-1T2015",
                [
                    {
                        "namespace": "verification",
                        "name": "verification",
                        "criteria": {},
                    },
                    {
                        "namespace": "reverification",
                        "name": "midterm",
                        "criteria": {},
                    },
                    {
                        "namespace": "proctored_exam",
                        "name": "final",
                        "criteria": {},
                    },
                    {
                        "namespace": "grade",
                        "name": "grade",
                        "criteria": {"min_grade": 0.8},
                    },
                ])

    Raises:
        InvalidCreditRequirements

    Returns:
        None
    """

    try:
        credit_course = CreditCourse.get_credit_course(course_key=course_key)
        for requirement in requirements:
            CreditRequirement.add_course_requirement(credit_course, requirement)
    except:  # pylint: disable=bare-except
        raise InvalidCreditRequirements


def get_credit_requirements(course_key, namespace=None):
    """ Returns the requirements of a given course and namespace

    Args:
        course_key(CourseKey): The identifier for course
        namespace(str): Namespace of requirements

    Example:
        >>> get_credit_requirements("course-v1-edX-DemoX-1T2015")
                {
                    requirements =
                    [
                        {
                            "namespace": "verification",
                            "name": "verification",
                            "criteria": {},
                        },
                        {
                            "namespace": "reverification",
                            "name": "midterm",
                            "criteria": {},
                        },
                        {
                            "namespace": "proctored_exam",
                            "name": "final",
                            "criteria": {},
                        },
                        {
                            "namespace": "grade",
                            "name": "grade",
                            "criteria": {"min_grade": 0.8},
                        },
                    ]
                }

    Returns:
        Dict of requirements in the given namespace
    """

    requirements = CreditRequirement.get_course_requirements(course_key, namespace)
    return [
        {
            "namespace": requirement.namespace,
            "name": requirement.name,
            "criteria": requirement.configuration
        }
        for requirement in requirements
    ]
