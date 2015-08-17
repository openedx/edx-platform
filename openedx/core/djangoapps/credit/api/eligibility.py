"""
APIs for configuring credit eligibility requirements and tracking
whether a user has satisfied those requirements.
"""

import logging

from openedx.core.djangoapps.credit.exceptions import InvalidCreditRequirements, InvalidCreditCourse
from openedx.core.djangoapps.credit.models import (
    CreditCourse,
    CreditRequirement,
    CreditRequirementStatus,
    CreditEligibility,
)


log = logging.getLogger(__name__)


def is_credit_course(course_key):
    """
    Check whether the course has been configured for credit.

    Args:
        course_key (CourseKey): Identifier of the course.

    Returns:
        bool: True iff this is a credit course.

    """
    return CreditCourse.is_credit_course(course_key=course_key)


def set_credit_requirements(course_key, requirements):
    """
    Add requirements to given course.

    Args:
        course_key(CourseKey): The identifier for course
        requirements(list): List of requirements to be added

    Example:
        >>> set_credit_requirements(
                "course-v1-edX-DemoX-1T2015",
                [
                    {
                        "namespace": "reverification",
                        "name": "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
                        "display_name": "Assessment 1",
                        "criteria": {},
                    },
                    {
                        "namespace": "proctored_exam",
                        "name": "i4x://edX/DemoX/proctoring-block/final_uuid",
                        "display_name": "Final Exam",
                        "criteria": {},
                    },
                    {
                        "namespace": "grade",
                        "name": "grade",
                        "display_name": "Grade",
                        "criteria": {"min_grade": 0.8},
                    },
                ])

    Raises:
        InvalidCreditRequirements

    Returns:
        None
    """

    invalid_requirements = _validate_requirements(requirements)
    if invalid_requirements:
        invalid_requirements = ", ".join(invalid_requirements)
        raise InvalidCreditRequirements(invalid_requirements)

    try:
        credit_course = CreditCourse.get_credit_course(course_key=course_key)
    except CreditCourse.DoesNotExist:
        raise InvalidCreditCourse()

    old_requirements = CreditRequirement.get_course_requirements(course_key=course_key)
    requirements_to_disable = _get_requirements_to_disable(old_requirements, requirements)
    if requirements_to_disable:
        CreditRequirement.disable_credit_requirements(requirements_to_disable)

    for order, requirement in enumerate(requirements):
        CreditRequirement.add_or_update_course_requirement(credit_course, requirement, order)


def get_credit_requirements(course_key, namespace=None):
    """
    Get credit eligibility requirements of a given course and namespace.

    Args:
        course_key(CourseKey): The identifier for course
        namespace(str): Namespace of requirements

    Example:
        >>> get_credit_requirements("course-v1-edX-DemoX-1T2015")
            {
                requirements =
                [
                    {
                        "namespace": "reverification",
                        "name": "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
                        "display_name": "Assessment 1",
                        "criteria": {},
                    },
                    {
                        "namespace": "proctored_exam",
                        "name": "i4x://edX/DemoX/proctoring-block/final_uuid",
                        "display_name": "Final Exam",
                        "criteria": {},
                    },
                    {
                        "namespace": "grade",
                        "name": "grade",
                        "display_name": "Grade",
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
            "display_name": requirement.display_name,
            "criteria": requirement.criteria
        }
        for requirement in requirements
    ]


def is_user_eligible_for_credit(username, course_key):
    """
    Returns a boolean indicating if the user is eligible for credit for
    the given course

    Args:
        username(str): The identifier for user
        course_key (CourseKey): The identifier for course

    Returns:
        True if user is eligible for the course else False
    """
    return CreditEligibility.is_user_eligible_for_credit(course_key, username)


def get_eligibilities_for_user(username):
    """
    Retrieve all courses for which the user is eligible for credit.

    Arguments:
        username (unicode): Identifier of the user.

    Example:
        >>> get_eligibilities_for_user("ron")
        [
            {
                "course_key": "edX/Demo_101/Fall",
                "deadline": "2015-10-23"
            },
            {
                "course_key": "edX/Demo_201/Spring",
                "deadline": "2015-11-15"
            },
            ...
        ]

    Returns: list

    """
    return [
        {
            "course_key": eligibility.course.course_key,
            "deadline": eligibility.deadline,
        }
        for eligibility in CreditEligibility.get_user_eligibilities(username)
    ]


def set_credit_requirement_status(username, course_key, req_namespace, req_name, status="satisfied", reason=None):
    """
    Update the user's requirement status.

    This will record whether the user satisfied or failed a particular requirement
    in a course.  If the user has satisfied all requirements, the user will be marked
    as eligible for credit in the course.

    Args:
        username (str): Username of the user
        course_key (CourseKey): Identifier for the course associated with the requirement.
        req_namespace (str): Namespace of the requirement (e.g. "grade" or "reverification")
        req_name (str): Name of the requirement (e.g. "grade" or the location of the ICRV XBlock)

    Keyword Arguments:
        status (str): Status of the requirement (either "satisfied" or "failed")
        reason (dict): Reason of the status

    Example:
        >>> set_credit_requirement_status(
                "staff",
                CourseKey.from_string("course-v1-edX-DemoX-1T2015"),
                "reverification",
                "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
                status="satisfied",
                reason={}
            )

    """
    # Check if we're already eligible for credit.
    # If so, short-circuit this process.
    if CreditEligibility.is_user_eligible_for_credit(course_key, username):
        log.info(
            u'Skipping update of credit requirement with namespace "%s" '
            u'and name "%s" because the user "%s" is already eligible for credit '
            u'in the course "%s".',
            req_namespace, req_name, username, course_key
        )
        return

    # Retrieve all credit requirements for the course
    # We retrieve all of them to avoid making a second query later when
    # we need to check whether all requirements have been satisfied.
    reqs = CreditRequirement.get_course_requirements(course_key)

    # Find the requirement we're trying to set
    req_to_update = next((
        req for req in reqs
        if req.namespace == req_namespace
        and req.name == req_name
    ), None)

    # If we can't find the requirement, then the most likely explanation
    # is that there was a lag updating the credit requirements after the course
    # was published.  We *could* attempt to create the requirement here,
    # but that could cause serious performance issues if many users attempt to
    # lock the row at the same time.
    # Instead, we skip updating the requirement and log an error.
    if req_to_update is None:
        log.error(
            (
                u'Could not update credit requirement in course "%s" '
                u'with namespace "%s" and name "%s" '
                u'because the requirement does not exist. '
                u'The user "%s" should have had his/her status updated to "%s".'
            ),
            unicode(course_key), req_namespace, req_name, username, status
        )
        return

    # Update the requirement status
    CreditRequirementStatus.add_or_update_requirement_status(
        username, req_to_update, status=status, reason=reason
    )

    # If we're marking this requirement as "satisfied", there's a chance
    # that the user has met all eligibility requirements.
    if status == "satisfied":
        CreditEligibility.update_eligibility(reqs, username, course_key)


def get_credit_requirement_status(course_key, username, namespace=None, name=None):
    """ Retrieve the user's status for each credit requirement in the course.

    Args:
        course_key (CourseKey): The identifier for course
        username (str): The identifier of the user

    Example:
        >>> get_credit_requirement_status("course-v1-edX-DemoX-1T2015", "john")

                [
                    {
                        "namespace": "reverification",
                        "name": "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
                        "display_name": "In Course Reverification",
                        "criteria": {},
                        "status": "failed",
                        "status_date": "2015-06-26 07:49:13",
                    },
                    {
                        "namespace": "proctored_exam",
                        "name": "i4x://edX/DemoX/proctoring-block/final_uuid",
                        "display_name": "Proctored Mid Term Exam",
                        "criteria": {},
                        "status": "satisfied",
                        "status_date": "2015-06-26 11:07:42",
                    },
                    {
                        "namespace": "grade",
                        "name": "i4x://edX/DemoX/proctoring-block/final_uuid",
                        "display_name": "Minimum Passing Grade",
                        "criteria": {"min_grade": 0.8},
                        "status": "failed",
                        "status_date": "2015-06-26 11:07:44",
                    },
                ]

    Returns:
        list of requirement statuses
    """
    requirements = CreditRequirement.get_course_requirements(course_key, namespace=namespace, name=name)
    requirement_statuses = CreditRequirementStatus.get_statuses(requirements, username)
    requirement_statuses = dict((o.requirement, o) for o in requirement_statuses)
    statuses = []
    for requirement in requirements:
        requirement_status = requirement_statuses.get(requirement)
        statuses.append({
            "namespace": requirement.namespace,
            "name": requirement.name,
            "display_name": requirement.display_name,
            "criteria": requirement.criteria,
            "status": requirement_status.status if requirement_status else None,
            "status_date": requirement_status.modified if requirement_status else None,
        })
    return statuses


def _get_requirements_to_disable(old_requirements, new_requirements):
    """
    Get the ids of 'CreditRequirement' entries to be disabled that are
    deleted from the courseware.

    Args:
        old_requirements(QuerySet): QuerySet of CreditRequirement
        new_requirements(list): List of requirements being added

    Returns:
        List of ids of CreditRequirement that are not in new_requirements
    """
    requirements_to_disable = []
    for old_req in old_requirements:
        found_flag = False
        for req in new_requirements:
            # check if an already added requirement is modified
            if req["namespace"] == old_req.namespace and req["name"] == old_req.name:
                found_flag = True
                break
        if not found_flag:
            requirements_to_disable.append(old_req.id)
    return requirements_to_disable


def _validate_requirements(requirements):
    """
    Validate the requirements.

    Args:
        requirements(list): List of requirements

    Returns:
        List of strings of invalid requirements
    """
    invalid_requirements = []
    for requirement in requirements:
        invalid_params = []
        if not requirement.get("namespace"):
            invalid_params.append("namespace")
        if not requirement.get("name"):
            invalid_params.append("name")
        if not requirement.get("display_name"):
            invalid_params.append("display_name")
        if "criteria" not in requirement:
            invalid_params.append("criteria")

        if invalid_params:
            invalid_requirements.append(
                u"{requirement} has missing/invalid parameters: {params}".format(
                    requirement=requirement,
                    params=invalid_params,
                )
            )
    return invalid_requirements
