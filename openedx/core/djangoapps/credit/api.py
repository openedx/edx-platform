""" Contains the APIs for course credit requirements
"""
from models import CreditRequirement, CreditCourse
from exceptions import InvalidCreditRequirements


def set_credit_requirements(course_key, requirements):
    """ Add requirements to given course

    Args:
        course_key(CourseKey): The identifier for course
        requirements(list): List of requirements to be added

    Example:
        >>> set_credit_requirements(
                "course-v1-ASUx-DemoX-1T2015",
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


def get_credit_requirements(course_key, namespacce=None):
    """ Returns the requirements of given course and namespace

    Args:
        course_key(CourseKey): The identifier for course
        namespace(str): Namespace of requirements

    Example:
        >>> get_credit_requirements("course-v1-ASUx-DemoX-1T2015")
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

    requirements = CreditRequirement.get_course_requirements(course_key, namespacce)
    return {
        "requirements": [
            {
                "namespace": requirement.namespace,
                "name": requirement.name,
                "criteria": requirement.configuration
            }
            for requirement in requirements
        ]
    }
