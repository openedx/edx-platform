"""
Certificates API

This provides APIs for generating course certificates asynchronously.

Other Django apps should use the API functions defined here in this module; other apps should not import the
certificates models or any other certificates modules.
"""


import logging
from datetime import datetime
from pytz import UTC

from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from eventtracking import tracker
from opaque_keys.edx.django.models import CourseKeyField
from organizations.api import get_course_organization_id

from common.djangoapps.student.api import is_user_enrolled_in_course
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.branding import api as branding_api
from lms.djangoapps.certificates.generation_handler import (
    can_generate_certificate_task as _can_generate_certificate_task,
    generate_certificate_task as _generate_certificate_task,
    generate_user_certificates as _generate_user_certificates,
    is_on_certificate_allowlist as _is_on_certificate_allowlist,
    is_using_v2_course_certificates as _is_using_v2_course_certificates,
    regenerate_user_certificates as _regenerate_user_certificates
)
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.certificates.models import (
    CertificateAllowlist,
    CertificateGenerationConfiguration,
    CertificateGenerationCourseSetting,
    CertificateInvalidation,
    CertificateTemplate,
    CertificateTemplateAsset,
    ExampleCertificateSet,
    GeneratedCertificate,
    certificate_status_for_student
)
from lms.djangoapps.certificates.queue import XQueueCertInterface
from lms.djangoapps.certificates.utils import (
    get_certificate_url as _get_certificate_url,
    has_html_certificates_enabled as _has_html_certificates_enabled
)
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

log = logging.getLogger("edx.certificate")
User = get_user_model()
MODES = GeneratedCertificate.MODES


def is_passing_status(cert_status):
    """
    Given the status of a certificate, return a boolean indicating whether
    the student passed the course.  This just proxies to the classmethod
    defined in models.py
    """
    return CertificateStatuses.is_passing_status(cert_status)


def _format_certificate_for_user(username, cert):
    """
    Helper function to serialize an user certificate.

    Arguments:
        username (unicode): The identifier of the user.
        cert (GeneratedCertificate): a user certificate

    Returns: dict
    """
    try:
        return {
            "username": username,
            "course_key": cert.course_id,
            "type": cert.mode,
            "status": cert.status,
            "grade": cert.grade,
            "created": cert.created_date,
            "modified": cert.modified_date,
            "is_passing": is_passing_status(cert.status),
            "is_pdf_certificate": bool(cert.download_url),
            "download_url": (
                cert.download_url or get_certificate_url(cert.user.id, cert.course_id, uuid=cert.verify_uuid,
                                                         user_certificate=cert)
                if cert.status == CertificateStatuses.downloadable
                else None
            ),
        }
    except CourseOverview.DoesNotExist:
        return None


def get_certificates_for_user(username):
    """
    Retrieve certificate information for a particular user.

    Arguments:
        username (unicode): The identifier of the user.

    Returns: list

    Example Usage:
    >>> get_certificates_for_user("bob")
    [
        {
            "username": "bob",
            "course_key": CourseLocator('edX', 'DemoX', 'Demo_Course', None, None),
            "type": "verified",
            "status": "downloadable",
            "download_url": "https://www.example.com/cert.pdf",
            "grade": "0.98",
            "created": 2015-07-31T00:00:00Z,
            "modified": 2015-07-31T00:00:00Z
        }
    ]

    """
    certs = []
    # Checks if certificates are not None before adding them to list
    for cert in GeneratedCertificate.eligible_certificates.filter(user__username=username).order_by("course_id"):
        formatted_cert = _format_certificate_for_user(username, cert)
        if formatted_cert:
            certs.append(formatted_cert)
    return certs


def get_certificate_for_user(username, course_key, format_results=True):
    """
    Retrieve certificate information for a particular user for a specific course.

    Arguments:
        username (unicode): The identifier of the user.
        course_key (CourseKey): A Course Key.
    Returns:
        A dict containing information about the certificate or, optionally,
        the GeneratedCertificate object itself.
    """
    try:
        cert = GeneratedCertificate.eligible_certificates.get(
            user__username=username,
            course_id=course_key
        )
    except GeneratedCertificate.DoesNotExist:
        return None

    if format_results:
        return _format_certificate_for_user(username, cert)
    else:
        return cert


def get_certificates_for_user_by_course_keys(user, course_keys):
    """
    Retrieve certificate information for a particular user for a set of courses.

    Arguments:
        user (User)
        course_keys (set[CourseKey])

    Returns: dict[CourseKey: dict]
        Mapping from course keys to dict of certificate data.
        Course keys for courses for which the user does not have a certificate
        will be omitted.
    """
    certs = GeneratedCertificate.eligible_certificates.filter(
        user=user, course_id__in=course_keys
    )
    return {
        cert.course_id: _format_certificate_for_user(user.username, cert)
        for cert in certs
    }


def get_recently_modified_certificates(course_keys=None, start_date=None, end_date=None, user_ids=None):
    """
    Returns a QuerySet of GeneratedCertificate objects filtered by the input
    parameters and ordered by modified_date.
    """
    cert_filter_args = {}

    if course_keys:
        cert_filter_args['course_id__in'] = course_keys

    if start_date:
        cert_filter_args['modified_date__gte'] = start_date

    if end_date:
        cert_filter_args['modified_date__lte'] = end_date

    if user_ids:
        cert_filter_args['user__id__in'] = user_ids

    return GeneratedCertificate.objects.filter(**cert_filter_args).order_by('modified_date')


def generate_user_certificates(student, course_key, insecure=False, generation_mode='batch', forced_grade=None):
    return _generate_user_certificates(student, course_key, insecure, generation_mode, forced_grade)


def regenerate_user_certificates(student, course_key, forced_grade=None, template_file=None, insecure=False):
    return _regenerate_user_certificates(student, course_key, forced_grade, template_file, insecure)


def can_generate_certificate_task(user, course_key):
    """
    Determine if we can create a task to generate a certificate for this user in this course run.

    This will return True if either:
    - the course run is using the allowlist and the user is on the allowlist, or
    - the course run is using v2 course certificates
    """
    return _can_generate_certificate_task(user, course_key)


def generate_certificate_task(user, course_key, generation_mode=None):
    """
    Create a task to generate a certificate for this user in this course run, if the user is eligible and a certificate
    can be generated.

    If the allowlist is enabled for this course run and the user is on the allowlist, the allowlist logic will be used.
    Otherwise, the regular course certificate generation logic will be used.

    Args:
        user: user for whom to generate a certificate
        course_key: course run key for which to generate a certificate
        generation_mode: Used when emitting an events. Options are "self" (implying the user generated the cert
            themself) and "batch" for everything else.
    """
    return _generate_certificate_task(user, course_key, generation_mode)


def certificate_downloadable_status(student, course_key):
    """
    Check the student existing certificates against a given course.
    if status is not generating and not downloadable or error then user can view the generate button.

    Args:
        student (user object): logged-in user
        course_key (CourseKey): ID associated with the course

    Returns:
        Dict containing student passed status also download url, uuid for cert if available
    """
    current_status = certificate_status_for_student(student, course_key)

    # If the certificate status is an error user should view that status is "generating".
    # On the back-end, need to monitor those errors and re-submit the task.

    response_data = {
        'is_downloadable': False,
        'is_generating': True if current_status['status'] in [CertificateStatuses.generating,  # pylint: disable=simplifiable-if-expression
                                                              CertificateStatuses.error] else False,
        'is_unverified': True if current_status['status'] == CertificateStatuses.unverified else False,  # pylint: disable=simplifiable-if-expression
        'download_url': None,
        'uuid': None,
    }

    course_overview = CourseOverview.get_from_id(course_key)
    if (
        not certificates_viewable_for_course(course_overview) and
        CertificateStatuses.is_passing_status(current_status['status']) and
        course_overview.certificate_available_date
    ):
        response_data['earned_but_not_available'] = True
        response_data['certificate_available_date'] = course_overview.certificate_available_date

    may_view_certificate = course_overview.may_certify()
    if current_status['status'] == CertificateStatuses.downloadable and may_view_certificate:
        response_data['is_downloadable'] = True
        response_data['download_url'] = current_status['download_url'] or get_certificate_url(
            student.id, course_key, current_status['uuid']
        )
        response_data['is_pdf_certificate'] = bool(current_status['download_url'])
        response_data['uuid'] = current_status['uuid']

    return response_data


def set_cert_generation_enabled(course_key, is_enabled):
    """Enable or disable self-generated certificates for a course.

    There are two "switches" that control whether self-generated certificates
    are enabled for a course:

    1) Whether the self-generated certificates feature is enabled.
    2) Whether self-generated certificates have been enabled for this particular course.

    The second flag should be enabled *only* when someone has successfully
    generated example certificates for the course.  This helps avoid
    configuration errors (for example, not having a template configured
    for the course installed on the workers).  The UI for the instructor
    dashboard enforces this constraint.

    Arguments:
        course_key (CourseKey): The course identifier.

    Keyword Arguments:
        is_enabled (boolean): If provided, enable/disable self-generated
            certificates for this course.

    """
    CertificateGenerationCourseSetting.set_self_generation_enabled_for_course(course_key, is_enabled)
    cert_event_type = 'enabled' if is_enabled else 'disabled'
    event_name = '.'.join(['edx', 'certificate', 'generation', cert_event_type])
    tracker.emit(event_name, {
        'course_id': str(course_key),
    })
    if is_enabled:
        log.info("Enabled self-generated certificates for course '%s'.", str(course_key))
    else:
        log.info("Disabled self-generated certificates for course '%s'.", str(course_key))


def is_certificate_invalidated(student, course_key):
    """Check whether the certificate belonging to the given student (in given course) has been invalidated.

    Arguments:
        student (user object): logged-in user
        course_key (CourseKey): The course identifier.

    Returns:
        Boolean denoting whether the certificate has been invalidated for this learner.
    """
    log.info(f"Checking if student {student.id} has an invalidated certificate in course {course_key}.")

    certificate = GeneratedCertificate.certificate_for_student(student, course_key)
    if certificate:
        return CertificateInvalidation.has_certificate_invalidation(student, course_key)

    return False


def cert_generation_enabled(course_key):
    """Check whether certificate generation is enabled for a course.

    There are two "switches" that control whether self-generated certificates
    are enabled for a course:

    1) Whether the self-generated certificates feature is enabled.
    2) Whether self-generated certificates have been enabled for this particular course.

    Certificates are enabled for a course only when both switches
    are set to True.

    Arguments:
        course_key (CourseKey): The course identifier.

    Returns:
        boolean: Whether self-generated certificates are enabled
            for the course.

    """
    return (
        CertificateGenerationConfiguration.current().enabled and
        CertificateGenerationCourseSetting.is_self_generation_enabled_for_course(course_key)
    )


def generate_example_certificates(course_key):
    """Generate example certificates for a course.

    Example certificates are used to validate that certificates
    are configured correctly for the course.  Staff members can
    view the example certificates before enabling
    the self-generated certificates button for students.

    Several example certificates may be generated for a course.
    For example, if a course offers both verified and honor certificates,
    examples of both types of certificate will be generated.

    If an error occurs while starting the certificate generation
    job, the errors will be recorded in the database and
    can be retrieved using `example_certificate_status()`.

    Arguments:
        course_key (CourseKey): The course identifier.

    Returns:
        None

    """
    xqueue = XQueueCertInterface()
    for cert in ExampleCertificateSet.create_example_set(course_key):
        xqueue.add_example_cert(cert)


def example_certificates_status(course_key):
    """Check the status of example certificates for a course.

    This will check the *latest* example certificate task.
    This is generally what we care about in terms of enabling/disabling
    self-generated certificates for a course.

    Arguments:
        course_key (CourseKey): The course identifier.

    Returns:
        list

    Example Usage:

        >>> from lms.djangoapps.certificates import api as certs_api
        >>> certs_api.example_certificates_status(course_key)
        [
            {
                'description': 'honor',
                'status': 'success',
                'download_url': 'https://www.example.com/abcd/honor_cert.pdf'
            },
            {
                'description': 'verified',
                'status': 'error',
                'error_reason': 'No template found!'
            }
        ]

    """
    return ExampleCertificateSet.latest_status(course_key)


def has_html_certificates_enabled(course_overview):
    return _has_html_certificates_enabled(course_overview)


def get_certificate_url(user_id=None, course_id=None, uuid=None, user_certificate=None):
    return _get_certificate_url(user_id, course_id, uuid, user_certificate)


def get_active_web_certificate(course, is_preview_mode=None):
    """
    Retrieves the active web certificate configuration for the specified course
    """
    certificates = getattr(course, 'certificates', {})
    configurations = certificates.get('certificates', [])
    for config in configurations:
        if config.get('is_active') or is_preview_mode:
            return config
    return None


def get_certificate_template(course_key, mode, language):
    """
    Retrieves the custom certificate template based on course_key, mode, and language.
    """
    template = None
    # fetch organization of the course
    org_id = get_course_organization_id(course_key)

    # only consider active templates
    active_templates = CertificateTemplate.objects.filter(is_active=True)

    if org_id and mode:  # get template by org, mode, and key
        org_mode_and_key_templates = active_templates.filter(
            organization_id=org_id,
            mode=mode,
            course_key=course_key
        )
        template = _get_language_specific_template_or_default(language, org_mode_and_key_templates)

    # since no template matched that course_key, only consider templates with empty course_key
    empty_course_key_templates = active_templates.filter(course_key=CourseKeyField.Empty)
    if not template and org_id and mode:  # get template by org and mode
        org_and_mode_templates = empty_course_key_templates.filter(
            organization_id=org_id,
            mode=mode
        )
        template = _get_language_specific_template_or_default(language, org_and_mode_templates)
    if not template and org_id:  # get template by only org
        org_templates = empty_course_key_templates.filter(
            organization_id=org_id,
            mode=None
        )
        template = _get_language_specific_template_or_default(language, org_templates)
    if not template and mode:  # get template by only mode
        mode_templates = empty_course_key_templates.filter(
            organization_id=None,
            mode=mode
        )
        template = _get_language_specific_template_or_default(language, mode_templates)
    return template if template else None


def _get_language_specific_template_or_default(language, templates):
    """
    Returns templates that match passed in language.
    Returns default templates If no language matches, or language passed is None
    """
    two_letter_language = _get_two_letter_language_code(language)

    language_or_default_templates = list(templates.filter(Q(language=two_letter_language)
                                                          | Q(language=None) | Q(language='')))
    language_specific_template = _get_language_specific_template(two_letter_language,
                                                                 language_or_default_templates)
    if language_specific_template:
        return language_specific_template
    else:
        return _get_all_languages_or_default_template(language_or_default_templates)


def _get_language_specific_template(language, templates):
    for template in templates:
        if template.language == language:
            return template
    return None


def _get_all_languages_or_default_template(templates):
    """
    Returns the first template that isn't language specific
    """
    for template in templates:
        if template.language == '':
            return template

    return templates[0] if templates else None


def _get_two_letter_language_code(language_code):
    """
    Shortens language to only first two characters (e.g. es-419 becomes es)
    This is needed because Catalog returns locale language which is not always a 2 letter code.
    """
    if language_code is None:
        return None
    elif language_code == '':
        return ''
    else:
        return language_code[:2]


def get_asset_url_by_slug(asset_slug):
    """
    Returns certificate template asset url for given asset_slug.
    """
    asset_url = ''
    try:
        template_asset = CertificateTemplateAsset.objects.get(asset_slug=asset_slug)
        asset_url = template_asset.asset.url
    except CertificateTemplateAsset.DoesNotExist:
        pass
    return asset_url


def get_certificate_header_context(is_secure=True):
    """
    Return data to be used in Certificate Header,
    data returned should be customized according to the site configuration.
    """
    data = dict(
        logo_src=branding_api.get_logo_url(is_secure),
        logo_url=branding_api.get_base_url(is_secure),
    )

    return data


def get_certificate_footer_context():
    """
    Return data to be used in Certificate Footer,
    data returned should be customized according to the site configuration.
    """
    data = dict()

    # get Terms of Service and Honor Code page url
    terms_of_service_and_honor_code = branding_api.get_tos_and_honor_code_url()
    if terms_of_service_and_honor_code != branding_api.EMPTY_URL:
        data.update({'company_tos_url': terms_of_service_and_honor_code})

    # get Privacy Policy page url
    privacy_policy = branding_api.get_privacy_url()
    if privacy_policy != branding_api.EMPTY_URL:
        data.update({'company_privacy_url': privacy_policy})

    # get About page url
    about = branding_api.get_about_url()
    if about != branding_api.EMPTY_URL:
        data.update({'company_about_url': about})

    return data


def certificates_viewable_for_course(course):
    """
    Returns True if certificates are viewable for any student enrolled in the course, False otherwise.
    """
    if course.self_paced:
        return True
    if (
        course.certificates_display_behavior in ('early_with_info', 'early_no_info')
        or course.certificates_show_before_end
    ):
        return True
    if (
        course.certificate_available_date
        and course.certificate_available_date <= datetime.now(UTC)
    ):
        return True
    if (
        course.certificate_available_date is None
        and course.has_ended()
    ):
        return True
    return False


def get_allowlisted_users(course_key):
    """
    Return the users who are on the allowlist for this course run
    """
    return User.objects.filter(certificateallowlist__course_id=course_key, certificateallowlist__allowlist=True)


def create_or_update_certificate_allowlist_entry(user, course_key, notes, enabled=True):
    """
    Update-or-create an allowlist entry for a student in a given course-run.
    """
    certificate_allowlist, created = CertificateAllowlist.objects.update_or_create(
        user=user,
        course_id=course_key,
        defaults={
            'allowlist': enabled,
            'notes': notes,
        }
    )

    log.info(f"Updated the allowlist of course {course_key} with student {user.id} and enabled={enabled}")

    return certificate_allowlist, created


def remove_allowlist_entry(user, course_key):
    """
    Removes an allowlist entry for a user in a given course-run. If a certificate exists for the student in the
    course-run we will also attempt to invalidate the it before removing them from the allowlist.

    Returns the result of the removal operation as a bool.
    """
    log.info(f"Removing student {user.id} from the allowlist in course {course_key}")
    deleted = False

    allowlist_entry = get_allowlist_entry(user, course_key)
    if allowlist_entry:
        certificate = get_certificate_for_user(user.username, course_key, False)
        if certificate:
            log.info(f"Invalidating certificate for student {user.id} in course {course_key} before allowlist removal.")
            certificate.invalidate(source='allowlist_removal')

        log.info(f"Removing student {user.id} from the allowlist in course {course_key}.")
        allowlist_entry.delete()
        deleted = True

    return deleted


def get_allowlist_entry(user, course_key):
    """
    Retrieves and returns an allowlist entry for a given learner and course-run.
    """
    log.info(f"Attempting to retrieve an allowlist entry for student {user.id} in course {course_key}.")
    try:
        allowlist_entry = CertificateAllowlist.objects.get(user=user, course_id=course_key)
    except ObjectDoesNotExist:
        log.warning(f"No allowlist entry found for student {user.id} in course {course_key}.")
        return None

    return allowlist_entry


def is_on_allowlist(user, course_key):
    """
    Determines if a learner has an active allowlist entry for a given course-run.
    """
    log.info(f"Checking if student {user.id} is on the allowlist in course {course_key}")
    return _is_on_certificate_allowlist(user, course_key)


def can_be_added_to_allowlist(user, course_key):
    """
    Determines if a student is able to be added to the allowlist in a given course-run.
    """
    log.info(f"Checking if student {user.id} in course {course_key} can be added to the allowlist.")

    if not is_user_enrolled_in_course(user, course_key):
        log.info(f"Student {user.id} is not enrolled in course {course_key}")
        return False

    if is_certificate_invalidated(user, course_key):
        log.info(f"Student {user.id} is on the certificate invalidation list for course {course_key}")
        return False

    if is_on_allowlist(user, course_key):
        log.info(f"Student {user.id} already appears on allowlist in course {course_key}")
        return False

    return True


def create_certificate_invalidation_entry(certificate, user_requesting_invalidation, notes):
    """
    Invalidates a certificate with the given certificate id.
    """
    log.info(f"Creating a certificate invalidation entry linked to certificate with id {certificate.id}.")
    certificate_invalidation, __ = CertificateInvalidation.objects.update_or_create(
        generated_certificate=certificate,
        defaults={
            'active': True,
            'invalidated_by': user_requesting_invalidation,
            'notes': notes,
        }
    )

    return certificate_invalidation


def get_certificate_invalidation_entry(certificate):
    """
    Retrieves and returns an certificate invalidation entry for a given certificate id.
    """
    log.info(f"Attempting to retrieve certificate invalidation entry for certificate with id {certificate.id}.")
    try:
        certificate_invalidation_entry = CertificateInvalidation.objects.get(generated_certificate=certificate)
    except ObjectDoesNotExist:
        log.warning(f"No certificate invalidation found linked to certificate with id {certificate.id}.")
        return None

    return certificate_invalidation_entry


def is_using_v2_course_certificates(course_key):
    """
    Determines if the given course run is using V2 of course certificates
    """
    return _is_using_v2_course_certificates(course_key)


def get_allowlist(course_key):
    """
    Return the certificate allowlist for the given course run
    """
    return CertificateAllowlist.get_certificate_allowlist(course_key)


def get_enrolled_allowlisted_users(course_key):
    """
    Get all users who:
    - are enrolled in this course run
    - are allowlisted in this course run
    """
    users = CourseEnrollment.objects.users_enrolled_in(course_key)
    return users.filter(
        certificateallowlist__course_id=course_key,
        certificateallowlist__allowlist=True
    )


def get_enrolled_allowlisted_not_passing_users(course_key):
    """
    Get all users who:
    - are enrolled in this course run
    - are allowlisted in this course run
    - do not have a course certificate with a passing status
    """
    users = get_enrolled_allowlisted_users(course_key)
    return users.exclude(
        generatedcertificate__course_id=course_key,
        generatedcertificate__status__in=CertificateStatuses.PASSED_STATUSES
    )
