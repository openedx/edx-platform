# encoding: utf-8
"""
Admin site configurations for verify_student.
"""

from config_models.admin import ConfigurationModelAdmin
from ratelimitbackend import admin
from verify_student.models import (
    IcrvStatusEmailsConfiguration,
    SkippedReverification,
    SoftwareSecurePhotoVerification,
    VerificationStatus,
)


class SoftwareSecurePhotoVerificationAdmin(admin.ModelAdmin):
    """
    Admin for the SoftwareSecurePhotoVerification table.
    """
    list_display = ('id', 'user', 'status', 'receipt_id', 'submitted_at', 'updated_at')
    raw_id_fields = ('user', 'reviewing_user')
    search_fields = (
        'receipt_id',
    )


class VerificationStatusAdmin(admin.ModelAdmin):
    """
    Admin for the VerificationStatus table.
    """
    list_display = ('timestamp', 'user', 'status', 'checkpoint')
    readonly_fields = ()
    search_fields = ('checkpoint__checkpoint_location', 'user__username')
    raw_id_fields = ('user',)

    def get_readonly_fields(self, request, obj=None):
        """When editing an existing record, all fields should be read-only.

        VerificationStatus records should be immutable; to change the user's
        status, create a new record with the updated status and a more
        recent timestamp.

        """
        if obj:
            return self.readonly_fields + ('status', 'checkpoint', 'user', 'response', 'error')
        return self.readonly_fields


class SkippedReverificationAdmin(admin.ModelAdmin):
    """Admin for the SkippedReverification table. """
    list_display = ('created_at', 'user', 'course_id', 'checkpoint')
    raw_id_fields = ('user',)
    readonly_fields = ('user', 'course_id')
    search_fields = ('user__username', 'course_id', 'checkpoint__checkpoint_location')

    def has_add_permission(self, request):
        """Skipped verifications can't be created in Django admin. """
        return False


admin.site.register(SoftwareSecurePhotoVerification, SoftwareSecurePhotoVerificationAdmin)
admin.site.register(SkippedReverification, SkippedReverificationAdmin)
admin.site.register(VerificationStatus, VerificationStatusAdmin)
admin.site.register(IcrvStatusEmailsConfiguration, ConfigurationModelAdmin)
