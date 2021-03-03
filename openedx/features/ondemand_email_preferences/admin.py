"""
Admin configurations for ondemand_email_preferences app
"""
from django.contrib import admin
from django.forms import ModelForm, Select

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.ondemand_email_preferences.models import OnDemandEmailPreferences


def get_all_on_demand_courses():
    return tuple((co.id, "%s -- %s" % (co.display_name, co.id)) for co in CourseOverview.objects.filter(
        self_paced=True, start__isnull=False, end__isnull=False).order_by('id'))


class OnDemandEmailPreferencesAdminForm(ModelForm):
    """
    Form for the OnDemandEmailPreferences admin to show courses that are self paced.
    """
    def __init__(self, *args, **kwargs):
        """
        Only show courses that are self paced.
        :param args:
        :param kwargs:
        """
        super(OnDemandEmailPreferencesAdminForm, self).__init__(*args, **kwargs)

        self.fields['course_id'].widget = Select(choices=get_all_on_demand_courses())

    class Meta:
        model = OnDemandEmailPreferences
        fields = ['user', 'course_id', 'is_enabled']


class OnDemandEmailPreferencesAdminModel(admin.ModelAdmin):
    """
    Django admin customizations for OnDemandEmailPreferences model.
    """
    form = OnDemandEmailPreferencesAdminForm
    list_display = ['user', 'course_id', 'is_enabled']
    search_fields = ('user__username', 'course_id',)
    raw_id_fields = ('user',)


admin.site.register(OnDemandEmailPreferences, OnDemandEmailPreferencesAdminModel)
