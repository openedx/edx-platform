"""
Contains the APIs for course credit requirements.
"""

import logging
import uuid

from django.db import transaction

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from student.models import User
from .exceptions import (
    InvalidCreditRequirements,
    InvalidCreditCourse,
    UserIsNotEligible,
    CreditProviderNotConfigured,
    RequestAlreadyCompleted,
    CreditRequestNotFound,
    InvalidCreditStatus,
)
from .models import (
    CreditCourse,
    CreditRequirement,
    CreditRequirementStatus,
    CreditRequest,
    CreditEligibility,
)
from .signature import signature, get_shared_secret_key

log = logging.getLogger(__name__)


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

    for requirement in requirements:
        CreditRequirement.add_or_update_course_requirement(credit_course, requirement)


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


@transaction.commit_on_success
def create_credit_request(course_key, provider_id, username):
    """
    Initiate a request for credit from a credit provider.

    This will return the parameters that the user's browser will need to POST
    to the credit provider.  It does NOT calculate the signature.

    Only users who are eligible for credit (have satisfied all credit requirements) are allowed to make requests.

    A provider can be configured either with *integration enabled* or not.
    If automatic integration is disabled, this method will simply return
    a URL to the credit provider and method set to "GET", so the student can
    visit the URL and request credit directly.  No database record will be created
    to track these requests.

    If automatic integration *is* enabled, then this will also return the parameters
    that the user's browser will need to POST to the credit provider.
    These parameters will be digitally signed using a secret key shared with the credit provider.

    A database record will be created to track the request with a 32-character UUID.
    The returned dictionary can be used by the user's browser to send a POST request to the credit provider.

    If a pending request already exists, this function should return a request description with the same UUID.
    (Other parameters, such as the user's full name may be different than the original request).

    If a completed request (either accepted or rejected) already exists, this function will
    raise an exception.  Users are not allowed to make additional requests once a request
    has been completed.

    Arguments:
        course_key (CourseKey): The identifier for the course.
        provider_id (str): The identifier of the credit provider.
        user (User): The user initiating the request.

    Returns: dict

    Raises:
        UserIsNotEligible: The user has not satisfied eligibility requirements for credit.
        CreditProviderNotConfigured: The credit provider has not been configured for this course.
        RequestAlreadyCompleted: The user has already submitted a request and received a response
            from the credit provider.

    Example Usage:
        >>> create_credit_request(course.id, "hogwarts", "ron")
        {
            "url": "https://credit.example.com/request",
            "method": "POST",
            "parameters": {
                "request_uuid": "557168d0f7664fe59097106c67c3f847",
                "timestamp": "2015-05-04T20:57:57.987119+00:00",
                "course_org": "HogwartsX",
                "course_num": "Potions101",
                "course_run": "1T2015",
                "final_grade": 0.95,
                "user_username": "ron",
                "user_email": "ron@example.com",
                "user_full_name": "Ron Weasley",
                "user_mailing_address": "",
                "user_country": "US",
                "signature": "cRCNjkE4IzY+erIjRwOQCpRILgOvXx4q2qvx141BCqI="
            }
        }

    """
    try:
        user_eligibility = CreditEligibility.objects.select_related('course', 'provider').get(
            username=username,
            course__course_key=course_key,
            provider__provider_id=provider_id
        )
        credit_course = user_eligibility.course
        credit_provider = user_eligibility.provider
    except CreditEligibility.DoesNotExist:
        log.warning(u'User tried to initiate a request for credit, but the user is not eligible for credit')
        raise UserIsNotEligible

    # Check if we've enabled automatic integration with the credit
    # provider.  If not, we'll show the user a link to a URL
    # where the user can request credit directly from the provider.
    # Note that we do NOT track these requests in our database,
    # since the state would always be "pending" (we never hear back).
    if not credit_provider.enable_integration:
        return {
            "url": credit_provider.provider_url,
            "method": "GET",
            "parameters": {}
        }
    else:
        # If automatic credit integration is enabled, then try
        # to retrieve the shared signature *before* creating the request.
        # That way, if there's a misconfiguration, we won't have requests
        # in our system that we know weren't sent to the provider.
        shared_secret_key = get_shared_secret_key(credit_provider.provider_id)
        if shared_secret_key is None:
            msg = u'Credit provider with ID "{provider_id}" does not have a secret key configured.'.format(
                provider_id=credit_provider.provider_id
            )
            log.error(msg)
            raise CreditProviderNotConfigured(msg)

    # Initiate a new request if one has not already been created
    credit_request, created = CreditRequest.objects.get_or_create(
        course=credit_course,
        provider=credit_provider,
        username=username,
    )

    # Check whether we've already gotten a response for a request,
    # If so, we're not allowed to issue any further requests.
    # Skip checking the status if we know that we just created this record.
    if not created and credit_request.status != "pending":
        log.warning(
            (
                u'Cannot initiate credit request because the request with UUID "%s" '
                u'exists with status "%s"'
            ), credit_request.uuid, credit_request.status
        )
        raise RequestAlreadyCompleted

    if created:
        credit_request.uuid = uuid.uuid4().hex

    # Retrieve user account and profile info
    user = User.objects.select_related('profile').get(username=username)

    # Retrieve the final grade from the eligibility table
    try:
        final_grade = CreditRequirementStatus.objects.filter(
            username=username,
            requirement__namespace="grade",
            requirement__name="grade",
            status="satisfied"
        ).latest().reason["final_grade"]
    except (CreditRequirementStatus.DoesNotExist, TypeError, KeyError):
        log.exception(
            "Could not retrieve final grade from the credit eligibility table "
            "for user %s in course %s.",
            user.id, course_key
        )
        raise UserIsNotEligible

    parameters = {
        "request_uuid": credit_request.uuid,
        "timestamp": credit_request.timestamp.isoformat(),
        "course_org": course_key.org,
        "course_num": course_key.course,
        "course_run": course_key.run,
        "final_grade": final_grade,
        "user_username": user.username,
        "user_email": user.email,
        "user_full_name": user.profile.name,
        "user_mailing_address": (
            user.profile.mailing_address
            if user.profile.mailing_address is not None
            else ""
        ),
        "user_country": (
            user.profile.country.code
            if user.profile.country.code is not None
            else ""
        ),
    }

    credit_request.parameters = parameters
    credit_request.save()

    if created:
        log.info(u'Created new request for credit with UUID "%s"', credit_request.uuid)
    else:
        log.info(
            u'Updated request for credit with UUID "%s" so the user can re-issue the request',
            credit_request.uuid
        )

    # Sign the parameters using a secret key we share with the credit provider.
    parameters["signature"] = signature(parameters, shared_secret_key)

    return {
        "url": credit_provider.provider_url,
        "method": "POST",
        "parameters": parameters
    }


def update_credit_request_status(request_uuid, provider_id, status):
    """
    Update the status of a credit request.

    Approve or reject a request for a student to receive credit in a course
    from a particular credit provider.

    This function does NOT check that the status update is authorized.
    The caller needs to handle authentication and authorization (checking the signature
    of the message received from the credit provider)

    The function is idempotent; if the request has already been updated to the status,
    the function does nothing.

    Arguments:
        request_uuid (str): The unique identifier for the credit request.
        provider_id (str): Identifier for the credit provider.
        status (str): Either "approved" or "rejected"

    Returns: None

    Raises:
        CreditRequestNotFound: No request exists that is associated with the given provider.
        InvalidCreditStatus: The status is not either "approved" or "rejected".

    """
    if status not in ["approved", "rejected"]:
        raise InvalidCreditStatus

    try:
        request = CreditRequest.objects.get(uuid=request_uuid, provider__provider_id=provider_id)
        old_status = request.status
        request.status = status
        request.save()

        log.info(
            u'Updated request with UUID "%s" from status "%s" to "%s" for provider with ID "%s".',
            request_uuid, old_status, status, provider_id
        )
    except CreditRequest.DoesNotExist:
        msg = (
            u'Credit provider with ID "{provider_id}" attempted to '
            u'update request with UUID "{request_uuid}", but no request '
            u'with this UUID is associated with the provider.'
        ).format(provider_id=provider_id, request_uuid=request_uuid)
        log.warning(msg)
        raise CreditRequestNotFound(msg)


def get_credit_requests_for_user(username):
    """
    Retrieve the status of a credit request.

    Returns either "pending", "accepted", or "rejected"

    Arguments:
        username (unicode): The username of the user who initiated the requests.

    Returns: list

    Example Usage:
    >>> get_credit_request_status_for_user("bob")
    [
        {
            "uuid": "557168d0f7664fe59097106c67c3f847",
            "timestamp": "2015-05-04T20:57:57.987119+00:00",
            "course_key": "course-v1:HogwartsX+Potions101+1T2015",
            "provider": {
                "id": "HogwartsX",
                "display_name": "Hogwarts School of Witchcraft and Wizardry",
            },
            "status": "pending"  # or "approved" or "rejected"
        }
    ]

    """
    return CreditRequest.credit_requests_for_user(username)


def get_credit_requirement_status(course_key, username):
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
                    },
                    {
                        "namespace": "proctored_exam",
                        "name": "i4x://edX/DemoX/proctoring-block/final_uuid",
                        "display_name": "Proctored Mid Term Exam",
                        "criteria": {},
                        "status": "satisfied",
                    },
                    {
                        "namespace": "grade",
                        "name": "i4x://edX/DemoX/proctoring-block/final_uuid",
                        "display_name": "Minimum Passing Grade",
                        "criteria": {"min_grade": 0.8},
                        "status": "failed",
                    },
                ]

    Returns:
        list of requirement statuses
    """
    requirements = CreditRequirement.get_course_requirements(course_key)
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


def is_user_eligible_for_credit(username, course_key):
    """Returns a boolean indicating if the user is eligible for credit for
    the given course

    Args:
        username(str): The identifier for user
        course_key (CourseKey): The identifier for course

    Returns:
        True if user is eligible for the course else False
    """
    return CreditEligibility.is_user_eligible_for_credit(course_key, username)


def get_credit_requirement(course_key, namespace, name):
    """Returns the requirement of a given course, namespace and name.

    Args:
        course_key(CourseKey): The identifier for course
        namespace(str): Namespace of requirement
        name(str): Name of the requirement

    Returns: dict

    Example:
    >>> get_credit_requirement_status(
        "course-v1-edX-DemoX-1T2015", "proctored_exam", "i4x://edX/DemoX/proctoring-block/final_uuid"
        )
            {
                "course_key": "course-v1-edX-DemoX-1T2015"
                "namespace": "reverification",
                "name": "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
                "display_name": "reverification"
                "criteria": {},
            }

    """
    requirement = CreditRequirement.get_course_requirement(course_key, namespace, name)
    return {
        "course_key": requirement.course.course_key,
        "namespace": requirement.namespace,
        "name": requirement.name,
        "display_name": requirement.display_name,
        "criteria": requirement.criteria
    } if requirement else None


def set_credit_requirement_status(username, requirement, status="satisfied", reason=None):
    """Update Credit Requirement Status for given username and requirement
        if exists else add new.

    Args:
        username(str): Username of the user
        requirement(dict): requirement dict
        status(str): Status of the requirement
        reason(dict): Reason of the status

    Example:
        >>> set_credit_requirement_status(
            "staff",
            {
                "course_key": "course-v1-edX-DemoX-1T2015"
                "namespace": "reverification",
                "name": "i4x://edX/DemoX/edx-reverification-block/assessment_uuid",
            },
            "satisfied",
            {}
            )

    """
    credit_requirement = CreditRequirement.get_course_requirement(
        requirement['course_key'], requirement['namespace'], requirement['name']
    )
    CreditRequirementStatus.add_or_update_requirement_status(
        username, credit_requirement, status, reason
    )


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


def is_credit_course(course_key):
    """API method to check if course is credit or not.

    Args:
        course_key(CourseKey): The course identifier string or CourseKey object

    Returns:
        Bool True if the course is marked credit else False

    """
    try:
        course_key = CourseKey.from_string(unicode(course_key))
    except InvalidKeyError:
        return False

    return CreditCourse.is_credit_course(course_key=course_key)
