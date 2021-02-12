"""
django admin pages for certificates models
"""
from django.contrib import admin

from lms.djangoapps.certificates.admin import GeneratedCertificateAdmin
from lms.djangoapps.certificates.models import GeneratedCertificate


class GeneratedCertificateAdminCustom(GeneratedCertificateAdmin):
    """
    Django admin customizations for GeneratedCertificate model
    """
    list_display = ('id', 'course_id', 'mode', 'user', 'verification_hash')
    readonly_fields = ('verification_hash',)

    def verification_hash(self, obj):
        if not hasattr(GeneratedCertificate, 'certificate_verification_key'):
            return

        return obj.certificate_verification_key.verification_key


admin.site.unregister(GeneratedCertificate)
admin.site.register(GeneratedCertificate, GeneratedCertificateAdminCustom)
