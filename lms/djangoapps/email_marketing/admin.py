""" Admin site bindings for email marketing """

from django.contrib import admin

from email_marketing.models import EmailMarketingConfiguration
from config_models.admin import ConfigurationModelAdmin

admin.site.register(EmailMarketingConfiguration, ConfigurationModelAdmin)
