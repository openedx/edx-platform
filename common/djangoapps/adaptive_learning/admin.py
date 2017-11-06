"""
Admin for Adaptive Learning
"""
from django.contrib import admin

from config_models.admin import ConfigurationModelAdmin

from adaptive_learning.config.models import AdaptiveLearningEnabledFlag

admin.site.register(AdaptiveLearningEnabledFlag, ConfigurationModelAdmin)
