import pdfkit

from datetime import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from constants import (
    COMPLETION_DATE_FORMAT,
    COURSE_URL_FMT,
    PDF_RESPONSE_HEADER,
    PDFKIT_IMAGE_PATH,
    TWITTER_META_TITLE_FMT)
from openedx.core.djangoapps.credentials.utils import get_credentials
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from util.philu_utils import date_from_str
from edxmako.shortcuts import render_to_response
from lms.djangoapps.philu_api.helpers import get_course_custom_settings

from certificates import api as certs_api
from courseware.courses import get_course
from lms.djangoapps.certificates.models import (
    GeneratedCertificate,
    CertificateStatuses)

from helpers import (
    get_certificate_image_url,
    get_certificate_image_url_by_uuid,
    get_image_and_size_from_url,
    get_pdfkit_html,
    get_pdfkit_options,
    get_philu_certificate_social_context
)
from models import CertificateVerificationKey


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

    user_certificates = []

    import json
    x = '{ "count": 1,"next": "","previous": "","results": [{"username": "edx","credential": {"type": "program","credential_id": 3,"program_uuid": "eb228773-a9a5-48cf-bb0e-94725d5aa4f1"},"status": "awarded","download_url": "","uuid": "5a1620c5-cb31-421e-b720-5704229d8c9a","attributes": [{"name": "program_name","value": "Test Discovery Program"}],"created": "2020-02-11T12:45:54Z","modified": "2020-03-27T16:43:59Z","certificate_url": "http://local.philanthropyu.org:18150/credentials/5a1620c5cb31421eb7205704229d8c9a/"}  ]}'
    context = json.loads(x)
    program_credentials = context['results']
    for credential in program_credentials:
        if 'certificate_url' in credential:
            program_name = [attribute['value'] for attribute in credential.get('attributes', {})
                            if 'name' in attribute and attribute['name'] == 'program_name']
            if program_name:
                user_certificates.append({
                    'certificate_name': program_name[0],
                    'certificate_title': program_name[0],
                    'certificate_url': credential.get('certificate_url'),
                    'completion_date': date_from_str(credential.get('created')).strftime(COMPLETION_DATE_FORMAT),
                    'is_program_cert': True,
                })

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
            'certificate_name': course_name,
            'certificate_title': course_title,
            'social_sharing_urls': get_philu_certificate_social_context(course, certificate),
            'certificate_url': "%s%s" % (settings.LMS_ROOT_URL, certificate_url),
            'course_start': start_date.strftime('%b %d, %Y') if start_date else None,
            'completion_date': completion_date.strftime('%b %d, %Y') if completion_date else None,
            'is_program_cert': False,
        })



    context = {
        'user_certificates': user_certificates,
    }

    response = render_to_response('certificates.html', context)
    return response


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
            base_url = settings.LMS_ROOT_URL,
            course_url = 'courses',
            course_id = course.id,
            about_url = 'about'
        ),
        'meta_tags': meta_tags,
    }

    response = render_to_response('shared_certificate.html', context)
    return response


@login_required
@ensure_csrf_cookie
def download_certificate_pdf(request, certificate_uuid):
    """
    Convert user certificate image on S3 bucket to PDF file and download it for end user
    :param request: HttpRequest obj
    :param certificate_uuid: certificate unique id
    :return: downloadable PDF file
    """

    certificate_image_url = get_certificate_image_url_by_uuid(certificate_uuid)
    image_base64, image_width, image_height = get_image_and_size_from_url(certificate_image_url)

    certificate_image_html = get_pdfkit_html(image_base64)
    pdfkit_options = get_pdfkit_options(image_width, image_height)

    pdf_document_object = pdfkit.from_string(certificate_image_html, PDFKIT_IMAGE_PATH, pdfkit_options)

    response_pdf_certificate = HttpResponse(pdf_document_object, content_type='application/pdf')
    response_pdf_certificate['Content-Disposition'] = PDF_RESPONSE_HEADER.format(certificate_pdf_name='certificate')

    return response_pdf_certificate


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
