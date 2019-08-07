""" Admin site bindings for email marketing """

from __future__ import absolute_import

from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from email_marketing.models import EmailMarketingConfiguration

admin.site.register(EmailMarketingConfiguration, ConfigurationModelAdmin)
