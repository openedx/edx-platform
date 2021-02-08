from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import ensure_csrf_cookie

from certificates import api as certs_api
from constants import COMPLETION_DATE_FORMAT, COURSE_URL_FMT, PDF_RESPONSE_HEADER, TWITTER_META_TITLE_FMT
from courseware.courses import get_course
from edxmako.shortcuts import render_to_response
from helpers import (
    get_certificate_image_url,
    get_certificate_pdf_name,
    get_credential_certificates,
    get_pdf_data_by_certificate_uuid,
    get_philu_certificate_social_context
)
from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate
from lms.djangoapps.philu_api.helpers import get_course_custom_settings
from models import CertificateVerificationKey
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


@login_required
@ensure_csrf_cookie
def student_certificates(request):
    """
    Provides the User with all certificates generated for the user

    Arguments:
        request: The request object.

    Returns:
        The generated certifcates list response.

    """
    from student.views import get_course_enrollments

    user = request.user

    # we want to filter and only show enrollments for courses within
    # the 'ORG' defined in configuration.
    course_org_filter = configuration_helpers.get_value('course_org_filter')

    # Let's filter out any courses in an "org" that has been declared to be
    # in a configuration
    org_filter_out_set = configuration_helpers.get_all_orgs()

    # remove our current org from the "filter out" list, if applicable
    if course_org_filter:
        org_filter_out_set.remove(course_org_filter)

    # Build our (course, enrollment) list for the user, but ignore any courses that no
    # longer exist (because the course IDs have changed). Still, we don't delete those
    # enrollments, because it could have been a data push snafu.
    course_enrollments = list(get_course_enrollments(user, course_org_filter, org_filter_out_set))

    # sort the enrollment pairs by the enrollment date
    course_enrollments.sort(key=lambda x: x.created, reverse=True)

    # Retrieve the course modes for each course
    enrolled_course_ids = [enrollment.course_id for enrollment in course_enrollments]

    user_certificates = get_credential_certificates(user)

    available_certificates = GeneratedCertificate.objects.filter(user=user, course_id__in=enrolled_course_ids).all()

    for certificate in available_certificates:
        certificate_url = None
        course_id = certificate.course_id
        course = get_course(course_id)
        cert_downloadable_status = certs_api.certificate_downloadable_status(user, course_id)

        if cert_downloadable_status['is_downloadable']:
            certificate_url = cert_downloadable_status['download_url']

            if certs_api.has_html_certificates_enabled(course):
                if certs_api.get_active_web_certificate(course) is not None:
                    certificate_url = certs_api.get_certificate_url(
                        course_id=course_id, uuid=cert_downloadable_status['uuid']
                    )
                else:
                    continue

        if not certificate_url:
            continue

        course_name = course.display_name

        start_date = course.start

        try:
            completion_date = course.end
        except Exception as ex:
            completion_date = datetime.now()

        try:
            course_title = course.certificates['certificates'].pop()['course_title']
        except IndexError as ex:
            course_title = course.display_name
        except TypeError as ex:
            course_title = course.display_name

        user_certificates.append({
            'display_name': course_name,
            'certificate_title': course_title,
            'social_sharing_urls': get_philu_certificate_social_context(course, certificate),
            'certificate_url': "%s%s" % (settings.LMS_ROOT_URL, certificate_url),
            'course_start': start_date.strftime(COMPLETION_DATE_FORMAT) if start_date else None,
            'completion_date': completion_date.strftime(COMPLETION_DATE_FORMAT) if completion_date else None,
            'is_program_cert': False,
        })

    context = {
        'user_certificates': user_certificates,
    }

    return render_to_response('certificates.html', context)


def shared_student_achievements(request, certificate_uuid):
    """
    Provides the User with the shared certificate page

    Arguments:
        request: The request object.

    Returns:
        The shared certificate response.

    """

    try:
        certificate = GeneratedCertificate.eligible_certificates.get(
            verify_uuid=certificate_uuid,
            status=CertificateStatuses.downloadable
        )
    except GeneratedCertificate.DoesNotExist:
        raise Http404

    course = get_course(certificate.course_id)

    custom_settings = get_course_custom_settings(course.id)
    meta_tags = custom_settings.get_course_meta_tags()

    meta_tags['description'] = meta_tags['description'] or ""
    meta_tags['title'] = TWITTER_META_TITLE_FMT.format(course_name=course.display_name)
    meta_tags['image'] = get_certificate_image_url(certificate)

    context = {
        'course_url': COURSE_URL_FMT.format(
            base_url=settings.LMS_ROOT_URL,
            course_url='courses',
            course_id=course.id,
            about_url='about'
        ),
        'meta_tags': meta_tags,
    }

    response = render_to_response('shared_certificate.html', context)
    return response


@login_required
@ensure_csrf_cookie
def download_certificate_pdf(request, certificate_uuid):
    """
    Convert user certificate image on S3 bucket to PDF and download it for end user
    Arguments:
        request: The HttpRequest object.
        certificate_uuid: certificate unique id.
    Returns:
        Downloadable PDF file.
    """
    pdf_data = get_pdf_data_by_certificate_uuid(certificate_uuid)
    pdf_name = get_certificate_pdf_name(certificate_uuid)
    response = HttpResponse(pdf_data, content_type='application/pdf')
    response['Content-Disposition'] = PDF_RESPONSE_HEADER.format(certificate_pdf_name=pdf_name)
    return response


def verify_certificate(request, key):
    """
    Provides verify certificate page
    Arguments:
        request: The request object.
        key: Verification key of certificate.
    Returns:
        The verify certificate response.
    """

    certificate_verification_key_obj = get_object_or_404(CertificateVerificationKey, verification_key=key)
    certificate = certificate_verification_key_obj.generated_certificate

    context = {
        'achieved_by': certificate.user.get_full_name(),
        'achieved_at': certificate.created_date.strftime('%B %d, %Y'),
        'course_name': get_course(certificate.course_id).display_name,
        'certificate_image': get_certificate_image_url(certificate)
    }

    return render_to_response('verify_certificate.html', context)
