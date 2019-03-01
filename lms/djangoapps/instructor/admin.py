from config_models.admin import ConfigurationModelAdmin
from django.forms import ModelForm
from django.contrib.admin import site, ModelAdmin
from config_models.models import ConfigurationModel
from django.contrib.sites.models import Site
from django.db.models import ForeignKey, CharField

from lms.djangoapps.instructor.models import CommunicatorConfig

class CommunicatorConfigAdmin(ModelAdmin):
    search_fields = ('course', 'site',)

    list_display = ('course', 'site', 'backend_url',)
    form = ModelForm

site.register(CommunicatorConfig, CommunicatorConfigAdmin)