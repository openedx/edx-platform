"""
Django admin page for credential
"""
from django.contrib import admin

from openedx.core.djangoapps.credentials_service.models import ( CertificateTemplate ,
    CourseCertificate, CertificateTemplateAsset, ProgramCertificate,
    Signatory, UserCredential,
    UserCredentialAttribute)


admin.site.register(CertificateTemplateAsset)
admin.site.register(CertificateTemplate)
admin.site.register(CourseCertificate)
admin.site.register(ProgramCertificate)
admin.site.register(Signatory)
admin.site.register(UserCredential)

admin.site.register(UserCredentialAttribute)
