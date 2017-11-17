from django.contrib import admin
from django import forms
from django.utils.translation import ugettext_lazy as _

from . import models


class ScheduleExperienceAdminInline(admin.StackedInline):
    model = models.ScheduleExperience


@admin.register(models.Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('username', 'course_id', 'active', 'start', 'upgrade_deadline')
    raw_id_fields = ('enrollment',)
    readonly_fields = ('modified',)
    search_fields = ('enrollment__user__username', 'enrollment__course__id',)
    inlines = (ScheduleExperienceAdminInline,)

    def username(self, obj):
        return obj.enrollment.user.username

    username.short_description = _('Username')

    def course_id(self, obj):
        return obj.enrollment.course_id

    course_id.short_description = _('Course ID')

    def get_queryset(self, request):
        qs = super(ScheduleAdmin, self).get_queryset(request)
        qs = qs.select_related('enrollment', 'enrollment__user')
        return qs


class ScheduleConfigAdminForm(forms.ModelForm):

    def clean_hold_back_ratio(self):
        hold_back_ratio = self.cleaned_data["hold_back_ratio"]
        if hold_back_ratio < 0 or hold_back_ratio > 1:
            raise forms.ValidationError("Invalid hold back ratio, the value must be between 0 and 1.")
        return hold_back_ratio


@admin.register(models.ScheduleConfig)
class ScheduleConfigAdmin(admin.ModelAdmin):
    search_fields = ('site',)
    list_display = (
        'site', 'create_schedules',
        'enqueue_recurring_nudge', 'deliver_recurring_nudge',
        'enqueue_upgrade_reminder', 'deliver_upgrade_reminder',
        'enqueue_course_update', 'deliver_course_update',
        'hold_back_ratio',
    )
    form = ScheduleConfigAdminForm
