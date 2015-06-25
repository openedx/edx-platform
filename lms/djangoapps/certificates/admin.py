"""
django admin pages for certificates models
"""
from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin
from certificates.models import CertificateGenerationConfiguration, CertificateHtmlViewConfiguration


admin.site.register(CertificateGenerationConfiguration)
admin.site.register(CertificateHtmlViewConfiguration, ConfigurationModelAdmin)
