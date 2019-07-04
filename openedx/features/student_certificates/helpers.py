import boto
from boto.s3.key import Key
from django.conf import settings

from lms.djangoapps.philu_api.helpers import get_course_custom_settings, get_social_sharing_urls
from constants import TWITTER_META_TITLE_FMT, SOCIAL_MEDIA_SHARE_URL_FMT, TWITTER_TWEET_TEXT_FMT

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
    return 'https://s3.amazonaws.com/{bucket}/{prefix}/{uuid}.jpg'.format(
        bucket=getattr(settings, "FILE_UPLOAD_STORAGE_BUCKET_NAME", None),
        prefix=CERTIFICATE_IMG_PREFIX,
        uuid=certificate.verify_uuid
    )


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
    return '/tmp/{img}'.format(img=img_name)


def get_certificate_img_key(img_name):
    """
    :param img_name:
    :return: return S3 key name for the image name
    """
    return '{prefix}/{img_name}'.format(prefix=CERTIFICATE_IMG_PREFIX, img_name=img_name)


def get_philu_certificate_social_context(course, certificate):
    custom_settings = get_course_custom_settings(certificate.course_id)
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
