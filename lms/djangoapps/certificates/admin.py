"""
django admin pages for certificates models
"""
from django.contrib import admin
from certificates.models import CertificateGenerationConfiguration


admin.site.register(CertificateGenerationConfiguration)
