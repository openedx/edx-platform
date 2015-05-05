from ratelimitbackend import admin
from verify_student.models import (
    SoftwareSecurePhotoVerification,
    InCourseReverificationConfiguration,
    VerificationStatus
)


class SoftwareSecurePhotoVerificationAdmin(admin.ModelAdmin):
    """
    Admin for the SoftwareSecurePhotoVerification table.
    """
    list_display = ('id', 'user', 'status', 'receipt_id', 'submitted_at', 'updated_at')
    search_fields = (
        'receipt_id',
    )


class VerificationStatusAdmin(admin.ModelAdmin):
    """
    Admin for the VerificationStatus table.
    """
    list_display = ('id', 'user', 'status', 'checkpoint', 'location_id')
    search_fields = (
        'checkpoint',
    )


admin.site.register(SoftwareSecurePhotoVerification, SoftwareSecurePhotoVerificationAdmin)
admin.site.register(InCourseReverificationConfiguration)
admin.site.register(VerificationStatus, VerificationStatusAdmin)
