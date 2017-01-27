"""Admin panel for configuring which user agents we consider to be Crawlers."""
from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin
from .models import CrawlersConfig

admin.site.register(CrawlersConfig, ConfigurationModelAdmin)
