"""
Helper methods to provide utility for student_certifications application.
"""
from datetime import datetime
from importlib import import_module
from io import BytesIO
from logging import getLogger

import img2pdf
import requests
from boto import connect_s3
from boto.s3.key import Key
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.urls import reverse

from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.philu_api.helpers import get_course_custom_settings, get_social_sharing_urls
from openedx.core.djangoapps.catalog.cache import PROGRAM_CACHE_KEY_TPL
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.credentials.utils import get_credentials
from openedx.features.student_certificates.constants import (
    CERTIFICATE_PDF_NAME,
    COMPLETION_DATE_FORMAT,
    CREDENTIALS_DATE_FORMAT,
    PREVIEW_CERTIFICATE_VERIFICATION_URL,
    SOCIAL_MEDIA_SHARE_URL_FMT,
    TMPDIR,
    TWITTER_META_TITLE_FMT
)
from openedx.features.student_certificates.signals import USER_CERTIFICATE_DOWNLOADABLE

log = getLogger(__name__)

certs_api = import_module('lms.djangoapps.certificates.api')
CERTIFICATE_IMG_PREFIX = 'certificates_images'


def upload_to_s3(file_path, s3_bucket, key_name):
    """
    :param file_path: path of the file we have to upload on s3
    :param s3_bucket: bucket in which we have to upload
    :param key_name: key by which we will place this file in the bucket
    :return:
    """
    aws_access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
    aws_secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
    conn = connect_s3(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

    bucket = conn.get_bucket(s3_bucket)
    key = Key(bucket=bucket, name=key_name)
    key.set_contents_from_filename(file_path)


def get_certificate_image_url(certificate):
    """
    :param certificate:
    :return: return s3 url of corresponding image of the certificate
    """
    return get_certificate_image_url_by_uuid(certificate.verify_uuid)


def get_certificate_image_url_by_uuid(verify_uuid):
    """
    :param certificate uuid:
    :return: return s3 url of corresponding image of the certificate
    """
    return 'https://s3.amazonaws.com/{bucket}/{prefix}/{uuid}.jpg'.format(
        bucket=getattr(settings, "FILE_UPLOAD_STORAGE_BUCKET_NAME", None),
        prefix=CERTIFICATE_IMG_PREFIX,
        uuid=verify_uuid
    )


def get_course_display_name_by_uuid(verify_uuid):
    """
    :param certificate uuid:
    :return: display name of the course
    """
    course_id = get_object_or_404(GeneratedCertificate, verify_uuid=verify_uuid).course_id
    course_display_name = CourseOverview.objects.get(id=course_id).display_name

    return course_display_name


def get_certificate_url(verify_uuid):
    """
    :param certificate:
    :return: url of the certificate
    """
    return '{root_url}/certificates/{uuid}?border=hide'.format(root_url=settings.LMS_ROOT_URL, uuid=verify_uuid)


def get_certificate_image_name(verify_uuid):
    """
    :param certificate:
    :return: image name of the certificate
    """
    return '{uuid}.jpg'.format(uuid=verify_uuid)


def get_certificate_image_path(img_name):
    """
    :param certificate:
    :return: image path of the certificate
    """
    return '{tmp_dir}/{img}'.format(tmp_dir=TMPDIR, img=img_name)


def get_certificate_img_key(img_name):
    """
    :param img_name:
    :return: return S3 key name for the image name
    """
    return '{prefix}/{img_name}'.format(prefix=CERTIFICATE_IMG_PREFIX, img_name=img_name)


def get_credential_certificates(user):
    """
    Retrieve all the certificates for the specified user

    Arguments:
        user (User): User for which to fetch the certificates

    Returns:
        list: A list containing data for certificates
    """
    certificates = []
    program_credentials = get_credentials(user, credential_type='program')
    for credential in program_credentials:
        certificate_url = credential.get('certificate_url')
        if not certificate_url:
            continue

        program_uuid = credential['credential']['program_uuid']
        program = cache.get(PROGRAM_CACHE_KEY_TPL.format(uuid=program_uuid))
        if not program:
            log.error('Program not found! Cache might be empty or does\'t contains program against uuid: {uuid}'
                      .format(uuid=program_uuid))
            continue

        program_name = program['title']
        completion_date = datetime.strptime(credential.get('created'), CREDENTIALS_DATE_FORMAT)
        certificates.append({
            'display_name': program_name,
            'certificate_title': program_name,
            'certificate_url': certificate_url,
            'completion_date': completion_date.strftime(COMPLETION_DATE_FORMAT),
            'is_program_cert': True,
        })
    return certificates


def get_philu_certificate_social_context(course, certificate):
    """
    Get course certificate urls for sharing on social sites

    Arguments:
         course (Course): Course which the urls are associated with
         certificate (GeneratedCertificate): Certificate for which to generate social urls

    Returns:
        dict: Dictionary containing the urls (value) for different social sites (key)
    """
    custom_settings = get_course_custom_settings(course.id)
    meta_tags = custom_settings.get_course_meta_tags()

    meta_tags['title'] = TWITTER_META_TITLE_FMT.format(course_name=course.display_name)

    social_sharing_urls = get_social_sharing_urls(SOCIAL_MEDIA_SHARE_URL_FMT.format(
        base_url=settings.LMS_ROOT_URL,
        certificate_uuid=certificate.verify_uuid), meta_tags)

    return social_sharing_urls


def get_pdf_data_by_certificate_uuid(uuid):
    """
    Get pdf data in bytes from certificate uuid.

    Get certificate image url by uuid, load image in a variable and convert it into pdf.

    Arguments:
        uuid: certificate unique id.
    Returns:
        Certificate pdf data
    """
    image_url = get_certificate_image_url_by_uuid(uuid)
    with requests.get(image_url, stream=True) as response:
        if response.status_code != 200:
            raise Exception('Unable to download certificate for url {}'.format(image_url), response.status_code)

        certificate_image = BytesIO(response.content)
        certificate_pdf_data = img2pdf.convert(certificate_image)

        return certificate_pdf_data


def get_certificate_pdf_name(certificate_uuid):
    """
    Get certificate PDF name

    Arguments:
        certificate_uuid: certificate unique id.
    Returns:
        Downloadable certificate PDF name
    """
    course_display_name = get_course_display_name_by_uuid(certificate_uuid)
    course_display_name = course_display_name.replace(' ', '')
    return CERTIFICATE_PDF_NAME.format(display_name=course_display_name)


def _should_hide_border(border, preview_mode):
    """Return true if certificate border is not required or preview mode is enabled"""
    return border == 'hide' or preview_mode


def override_update_certificate_context(request, context, course, user_certificate, preview_mode=None):
    """
    This method adds custom context to the certificate
    :return: Updated context
    """
    border = request.GET.get('border', None)

    context['border_class'] = 'certificate-border-hide' if _should_hide_border(border, preview_mode) else ''

    context['download_pdf'] = reverse('download_certificate_pdf',
                                      kwargs={'certificate_uuid': user_certificate.verify_uuid})
    context['social_sharing_urls'] = get_philu_certificate_social_context(course, user_certificate)

    context['verification_url'] = get_verification_url(user_certificate)


def get_verification_url(user_certificate):
    """
    Get verification url for the given user certificate

    Arguments:
        user_certificate (GeneratedCertificate): User certificate to get the verification url for

    Returns:
        str: Url for verification of the specified certificate
    """
    verification_url = PREVIEW_CERTIFICATE_VERIFICATION_URL
    if user_certificate.pk:
        verification_url = '{}{}'.format(
            settings.LMS_ROOT_URL,
            user_certificate.certificate_verification_key.verification_url
        )
    return verification_url


def fire_send_email_signal(course, cert):
    certificate_reverse_url = certs_api.get_certificate_url(user_id=cert.user.id, course_id=course.id,
                                                            uuid=cert.verify_uuid)
    certificate_url = settings.LMS_ROOT_URL + certificate_reverse_url
    USER_CERTIFICATE_DOWNLOADABLE.send(sender=GeneratedCertificate, first_name=cert.name,
                                       display_name=course.display_name,
                                       certificate_reverse_url=certificate_url,
                                       user_email=cert.user.email)
