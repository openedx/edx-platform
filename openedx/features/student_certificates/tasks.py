"""
Tasks for the student_certificate application
"""
from logging import getLogger
from os import remove

import imgkit
from celery.task import task
from django.conf import settings

from openedx.features.student_certificates.helpers import (
    get_certificate_image_name,
    get_certificate_image_path,
    get_certificate_img_key,
    get_certificate_url,
    upload_to_s3
)

log = getLogger(__name__)


@task(routing_key=settings.HIGH_MEM_QUEUE, max_retries=0)
def task_create_certificate_img_and_upload_to_s3(verify_uuid):
    """
    :param certificate:
    :return:
    """
    try:
        url = get_certificate_url(verify_uuid)
        img_name = get_certificate_image_name(verify_uuid)
        img_path = get_certificate_image_path(img_name)
        # creating image from certificate url
        imgkit.from_url(url, img_path)
        log.info('Certificate image created for verify_uuid:{uuid}'.format(uuid=verify_uuid))
        # uploading image to s3
        img_key = get_certificate_img_key(img_name)
        bucket_name = getattr(settings, "FILE_UPLOAD_STORAGE_BUCKET_NAME", None)
        upload_to_s3(img_path, bucket_name, img_key)
        log.info('Certificate image uploaded to S3 for verify_uuid:{uuid}'.format(uuid=verify_uuid))
        # Deleting image from local
        remove(img_path)
        log.info('Certificate image removed from local for verify_uuid:{uuid}'.format(uuid=verify_uuid))
    except Exception as ex:  # pylint: disable=broad-except
        log.error('Certificate image creation task failed, Reason: %s', ex.message)
