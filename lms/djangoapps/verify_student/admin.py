# encoding: utf-8
"""
Admin site configurations for verify_student.
"""

import os
import base64
import logging
import datetime
import requests
from django.contrib import admin
from django.conf import settings
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification, SSOVerification, ManualVerification
from lms.djangoapps.verify_student.ssencrypt import decode_and_decrypt, rsa_decrypt
from lms.djangoapps.verify_student.tasks import send_verification_status_email
from lms.djangoapps.verify_student.utils import aliyun_oss_storage_path
from openedx.core.storage import get_storage

log = logging.getLogger(__name__)


@admin.register(SoftwareSecurePhotoVerification)
class SoftwareSecurePhotoVerificationAdmin(admin.ModelAdmin):
    """
    Admin for the SoftwareSecurePhotoVerification table.
    """
    list_display = ('id', 'user', 'status', 'receipt_id', 'submitted_at', 'updated_at',)
    raw_id_fields = ('user', 'reviewing_user', 'copy_id_photo_from',)
    search_fields = ('receipt_id', 'user__username',)
    readonly_fields = ('face_image', 'photo_id_image',)

    def save_model(self, request, obj, form, change):
        status_pre = obj.status_changed
        super(SoftwareSecurePhotoVerificationAdmin, self).save_model(request, obj, form, change)
        status_changed = obj.status_changed
        if status_pre != status_changed and obj.status in ('approved', 'denied'):
            self._notify_user(obj)

    def get_image(self, file_name, aes_key):
        """
        decrypt image
        """
        resp = requests.get(self._storage.url(file_name, 5))
        image = decode_and_decrypt(resp.content, aes_key)
        return mark_safe(u'<img src="data:image/png;base64,{data}" width="500px" />'.format(
            data=base64.b64encode(image)))

    def face_image(self, obj):
        """
        show face image
        """
        try:
            aes_key = settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["FACE_IMAGE_AES_KEY"].decode("hex")
            file_name = self._get_path(obj, 'face')
            return self.get_image(file_name, aes_key)
        except Exception, e:
            log.exception(e)
        return None

    face_image.short_description = u'Face Image'

    def photo_id_image(self, obj):
        """
        show photo id image
        """
        try:
            rsa_private_key = settings.VERIFY_STUDENT["SOFTWARE_SECURE"]["RSA_PRIVATE_KEY"]
            aes_key = rsa_decrypt(obj.photo_id_key.decode('base64'), rsa_private_key)
            file_name = self._get_path(obj, 'photo_id')
            return self.get_image(file_name, aes_key)
        except Exception, e:
            log.exception(e)
        return None

    photo_id_image.short_description = u'PhotoID Image'

    @cached_property
    def _storage(self):
        """
        Return the configured django storage backend.
        """
        config = settings.VERIFY_STUDENT["SOFTWARE_SECURE"]
        storage_class = config.get("STORAGE_CLASS", "")
        storage_kwargs = config.get("STORAGE_KWARGS", {})
        return get_storage(storage_class, **storage_kwargs)

    @method_decorator(aliyun_oss_storage_path)
    def _get_path(self, obj, prefix, override_receipt_id=None):
        """
        Returns the path to a resource with this instance's `receipt_id`.
        """
        receipt_id = obj.receipt_id if override_receipt_id is None else override_receipt_id
        return os.path.join(prefix, receipt_id)

    def _notify_user(self, obj):
        """
        Send reviewing result email to user
        """
        try:
            user = obj.user
            verification_status_email_vars = {
                'platform_name': settings.PLATFORM_NAME,
            }
            if obj.status not in ('approved', 'denied'):
                return
            elif obj.status == 'approved':
                log.info("Approving verification for %s", obj.receipt_id)
                expiry_date = datetime.date.today() + datetime.timedelta(
                    days=settings.VERIFY_STUDENT["DAYS_GOOD_FOR"]
                )
                verification_status_email_vars['expiry_date'] = expiry_date.strftime("%m/%d/%Y")
                verification_status_email_vars['full_name'] = user.profile.name
                subject = _("Your {platform_name} ID Verification Approved").format(
                    platform_name=settings.PLATFORM_NAME
                )
                template_name = 'emails/passed_verification_email.txt'
            else:
                log.info("Denying verification for %s", obj.receipt_id)
                reverify_url = '{}{}'.format(settings.LMS_ROOT_URL, reverse("verify_student_reverify"))
                verification_status_email_vars['reasons'] = obj.error_msg
                verification_status_email_vars['reverify_url'] = reverify_url
                verification_status_email_vars['faq_url'] = settings.ID_VERIFICATION_SUPPORT_LINK
                subject = _("Your {platform_name} Verification Has Been Denied").format(
                    platform_name=settings.PLATFORM_NAME
                )
                template_name = 'emails/failed_verification_email.txt'

            context = {
                'subject': subject,
                'template': template_name,
                'email': user.email,
                'email_vars': verification_status_email_vars
            }
            send_verification_status_email.delay(context)
        except Exception, e:
            log.exception(e)


@admin.register(SSOVerification)
class SSOVerificationAdmin(admin.ModelAdmin):
    """
    Admin for the SSOVerification table.
    """
    list_display = ('id', 'user', 'status', 'identity_provider_slug', 'created_at', 'updated_at',)
    readonly_fields = ('user', 'identity_provider_slug', 'identity_provider_type',)
    raw_id_fields = ('user',)
    search_fields = ('user__username', 'identity_provider_slug',)


@admin.register(ManualVerification)
class ManualVerificationAdmin(admin.ModelAdmin):
    """
    Admin for the ManualVerification table.
    """
    list_display = ('id', 'user', 'status', 'reason', 'created_at', 'updated_at',)
    raw_id_fields = ('user',)
    search_fields = ('user__username', 'reason',)
