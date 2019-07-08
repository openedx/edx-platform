from django.db.models.signals import post_save
from django.dispatch import receiver

from certificates.models import GeneratedCertificate

from tasks import task_create_certificate_img_and_upload_to_s3


@receiver(post_save, sender=GeneratedCertificate)
def generate_certificate_img(instance, created, **kwargs):
    if not created:
        task_create_certificate_img_and_upload_to_s3.delay(instance.verify_uuid)
