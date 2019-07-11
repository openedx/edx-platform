
import logging

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from lms.djangoapps.instructor.enrollment import (
    enroll_email,
    get_email_params,
    get_user_email_language,
    send_beta_role_email,
    send_mail_to_student,
    unenroll_email
)

from lms.djangoapps.instructor.views.tools import get_student_from_identifier

from openedx.core.djangoapps.appsembler.api.sites import (
    get_site_for_course
)

from student.models import (
    ALLOWEDTOENROLL_TO_ENROLLED,
    ENROLLED_TO_ENROLLED,
    DEFAULT_TRANSITION_STATE,
    UNENROLLED_TO_ENROLLED,
    UNENROLLED_TO_ALLOWEDTOENROLL,
    ManualEnrollmentAudit
)

from organizations.models import (
    OrganizationCourse,
    UserOrganizationMapping,
)


log = logging.getLogger(__name__)


def enroll_learners_in_course(course_id, identifiers, enroll_func, **kwargs):
    """
    This method assumes that the site has been verified to own this course

    This method is a quick hack. It copies from the existing appsembler_api
    from Ginkgo. See:
        lms/djangoapps/instructor/views/api.py:students_update_enrollment

    ## Operational notes

    If a user does not already exist then a new entry is created in
    `CourseEnrollmentAllowed`. This is default behavior, not a new addition of
    this API.


    ## Future Design and considerations
    - We want to decouple concerns
        - email notification is a seperate method or class

    - Move the inner code it's own function. Probably make the outer an iterator
      on the identifiers
    """

    reason = kwargs.get('reason', u'')
    request_user = kwargs.get('request_user')
    role = kwargs.get('role')

    results = []
    site = get_site_for_course(course_id)
    org = OrganizationCourse.objects.get(course_id=str(course_id))

    enrollment_obj = None
    state_transition = DEFAULT_TRANSITION_STATE

    for identifier in identifiers:
        user = None
        email = None
        language = None
        try:
            user = get_student_from_identifier(identifier)
        except User.DoesNotExist:
            email = identifier
        else:
            email = user.email
            language = get_user_email_language(user)

        try:
            # Use django.core.validators.validate_email to check email address
            # validity (obviously, cannot check if email actually /exists/,
            # simply that it is plausibly valid)
            validate_email(email)  # Raises ValidationError if invalid
            before, after, enrollment_obj = enroll_func(course_id=course_id,
                                                        student_email=email,
                                                        language=language)
            before_enrollment = before.to_dict()['enrollment']
            before_user_registered = before.to_dict()['user']
            before_allowed = before.to_dict()['allowed']
            after_enrollment = after.to_dict()['enrollment']
            after_allowed = after.to_dict()['allowed']

            if before_user_registered:
                if after_enrollment:
                    if before_enrollment:
                        state_transition = ENROLLED_TO_ENROLLED
                    else:
                        if before_allowed:
                            state_transition = ALLOWEDTOENROLL_TO_ENROLLED
                        else:
                            state_transition = UNENROLLED_TO_ENROLLED
            else:
                if after_allowed:
                    state_transition = UNENROLLED_TO_ALLOWEDTOENROLL

        except ValidationError:
            # Flag this email as an error if invalid, but continue checking
            # the remaining in the list
            results.append({
                'identifier': identifier,
                'invalidIdentifier': True,
            })

        except Exception as exc:  # pylint: disable=broad-except
            # catch and log any exceptions
            # so that one error doesn't cause a 500.
            log.exception(u"Error while #{}ing student")
            log.exception(exc)
            results.append({
                'identifier': identifier,
                'error': True,
                'error_message': str(exc),
            })

        else:
            ManualEnrollmentAudit.create_manual_enrollment_audit(
                request_user, email, state_transition, reason, enrollment_obj, role
            )
            results.append({
                'identifier': identifier,
                'before': before.to_dict(),
                'after': after.to_dict(),
            })
    return results
