""" Admin site bindings for email marketing """


from config_models.admin import ConfigurationModelAdmin
from django.contrib import admin

from .models import EmailMarketingConfiguration

admin.site.register(EmailMarketingConfiguration, ConfigurationModelAdmin)
