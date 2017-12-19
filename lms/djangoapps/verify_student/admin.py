# encoding: utf-8
"""
Admin site configurations for verify_student.
"""

from django.contrib import admin

from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification


@admin.register(SoftwareSecurePhotoVerification)
class SoftwareSecurePhotoVerificationAdmin(admin.ModelAdmin):
    """
    Admin for the SoftwareSecurePhotoVerification table.
    """
    list_display = ('id', 'user', 'status', 'receipt_id', 'submitted_at', 'updated_at',)
    raw_id_fields = ('user', 'reviewing_user', 'copy_id_photo_from',)
    search_fields = ('receipt_id', 'user__username',)
