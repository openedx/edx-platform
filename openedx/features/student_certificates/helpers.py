import base64
import shutil
from datetime import datetime
from importlib import import_module
from logging import getLogger
from tempfile import TemporaryFile

import boto
import requests
from boto.s3.key import Key
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.urls import reverse
from PIL import Image

from constants import (
    COMPLETION_DATE_FORMAT,
    CREDENTIALS_DATE_FORMAT,
    PAGE_HEIGHT,
    PAGE_WIDTH,
    PDFKIT_HTML_STRING,
    PDFKIT_IMAGE_TAG,
    PDFKIT_OPTIONS,
    PREVIEW_CERTIFICATE_VERIFICATION_URL,
    SOCIAL_MEDIA_SHARE_URL_FMT,
    TMPDIR,
    TWITTER_META_TITLE_FMT,
    TWITTER_TWEET_TEXT_FMT
)
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.philu_api.helpers import get_course_custom_settings, get_social_sharing_urls
from openedx.core.djangoapps.catalog.cache import PROGRAM_CACHE_KEY_TPL
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.credentials.utils import get_credentials
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
    conn = boto.connect_s3(
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
    custom_settings = get_course_custom_settings(course.id)
    meta_tags = custom_settings.get_course_meta_tags()

    tweet_text = TWITTER_TWEET_TEXT_FMT.format(
        course_name=course.display_name,
        base_url=settings.LMS_ROOT_URL,
        course_url='courses',
        course_id=course.id,
        about_url='about')

    meta_tags['title'] = TWITTER_META_TITLE_FMT.format(course_name=course.display_name)

    social_sharing_urls = get_social_sharing_urls(SOCIAL_MEDIA_SHARE_URL_FMT.format(
        base_url=settings.LMS_ROOT_URL,
        certificate_uuid=certificate.verify_uuid), meta_tags, tweet_text)

    return social_sharing_urls


def get_image_and_size_from_url(url):
    """
    Download image from url to a temp file, get image dimensions and encode to base64
    :param url: image url
    :return: base64 image, image width and image height
    """
    with requests.get(url, stream=True) as response:
        if response.status_code != 200:
            raise Exception("Unable to download certificate for url {}".format(url), response.status_code)

        with TemporaryFile(dir=TMPDIR) as certificate_image_file:
            # copy the contents of image request to our temporary file
            shutil.copyfileobj(response.raw, certificate_image_file)
            certificate_image_file.seek(0)  # file will be read from beginning
            image_base64 = base64.b64encode(certificate_image_file.read())
            image_file = Image.open(certificate_image_file)
            page_width, page_height = image_file.size
    return image_base64, page_width, page_height


def get_pdfkit_options(image_width, image_height):
    """
    Add image width and height in to pdfkit options
    :param image_width: image width in pixel
    :param image_height: image height in pixel
    :return: pdfkit options dict
    """
    PDFKIT_OPTIONS[PAGE_HEIGHT] = PDFKIT_OPTIONS[PAGE_HEIGHT].format(image_height)
    PDFKIT_OPTIONS[PAGE_WIDTH] = PDFKIT_OPTIONS[PAGE_WIDTH].format(image_width)

    return PDFKIT_OPTIONS


def get_pdfkit_html(image_base64):
    """
    Create basic html template with base64 image source. Due to bug in pdfkit, body and html
    need 0 padding style, otherwise image tag would have sufficed
    :param image_base64:
    :return: html
    """
    return PDFKIT_HTML_STRING.format(image_tag=PDFKIT_IMAGE_TAG.format(base64_img=image_base64))


def override_update_certificate_context(request, context, course, user_certificate, preview_mode=None):
    """
    This method adds custom context to the certificate
    :return: Updated context
    """
    border = request.GET.get('border', None)
    if (border and border == 'hide') or preview_mode:
        context['border_class'] = 'certificate-border-hide'
    else:
        context['border_class'] = ''

    context['download_pdf'] = reverse('download_certificate_pdf',
                                      kwargs={'certificate_uuid': user_certificate.verify_uuid})
    context['social_sharing_urls'] = get_philu_certificate_social_context(course, user_certificate)

    context['verification_url'] = get_verification_url(user_certificate)


def get_verification_url(user_certificate):
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
