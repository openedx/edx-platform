import base64
import pdfkit
import requests
import shutil

from datetime import datetime
from tempfile import TemporaryFile
from PIL import Image

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from constants import TWITTER_META_TITLE_FMT, COURSE_URL_FMT
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from edxmako.shortcuts import render_to_response
from lms.djangoapps.philu_api.helpers import get_course_custom_settings

from certificates import api as certs_api
from courseware.courses import get_course
from lms.djangoapps.certificates.models import (
    GeneratedCertificate,
    CertificateStatuses)

from helpers import (
    get_certificate_image_url,
    get_philu_certificate_social_context,
    get_certificate_image_url_by_uuid
)


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
            'course_name': course_name,
            'course_title': course_title,
            'social_sharing_urls': get_philu_certificate_social_context(course, certificate),
            'certificate_url': "%s%s" % (settings.LMS_ROOT_URL, certificate_url),
            'course_start': start_date.strftime('%b %d, %Y') if start_date else None,
            'completion_date': completion_date.strftime('%b %d, %Y') if completion_date else None,
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


def download_certificate_pdf(request, certificate_uuid):
    """
    Convert user certificate image on S3 bucket to PDF file and download it for end user
    :param request: HttpRequest obj
    :param certificate_uuid: certificate unique id
    :return: downloadable PDF file
    """

    url = get_certificate_image_url_by_uuid(certificate_uuid)

    with requests.get(url, stream=True) as req:
        if req.status_code != 200:
            raise Exception("Unable to download certificate")

        with TemporaryFile() as temp_file:
            shutil.copyfileobj(req.raw, temp_file)
            temp_file.seek(0)
            image_base64 = base64.b64encode(temp_file.read())
            image_file = Image.open(temp_file)
            page_width, page_height = image_file.size

    options = {
        'page-width': '{}px'.format(page_width),
        'page-height': '{}px'.format(page_height),
        'margin-left': '0.0in',
        'margin-right': '0.0in',
        'margin-bottom': '0.0in',
        'margin-top': '0.0in',
        'encoding': "UTF-8",
        'no-outline': None,
        'disable-smart-shrinking': None,
        'print-media-type': None
    }

    # Creating html to add certificate image. Due to bug in pdfkit, body and html
    # need 0 padding style, otherwise image tag would have sufficed
    img = '<img src="data:image/png;base64,%s"/>' % image_base64
    html = '<html><head><style>body,html{padding:0;margin:0;font-size:0;}</style></head><body>%s</body></html>' % img

    # Use false instead of output path to save pdf to a variable
    pdf = pdfkit.from_string(html, False, options)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="certificate.pdf"'
    return response
