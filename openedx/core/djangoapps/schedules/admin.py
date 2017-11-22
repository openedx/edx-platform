import functools

from django.contrib import admin
from django import forms
from django.db.models import F
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from . import models


class ScheduleExperienceAdminInline(admin.StackedInline):
    model = models.ScheduleExperience


def _set_experience(db_name, human_name, modeladmin, request, queryset):
    """
    A django action which will set all selected schedules to the supplied experience.
    The intended usage is with functools.partial to generate the action for each experience type
    dynamically.

    Arguments:
        db_name: the database name of the experience being selected
        human_name: the human name of the experience being selected
        modeladmin: The ModelAdmin subclass, passed by django as part of the standard Action interface
        request: The current request, passed by django as part of the standard Action interface
        queryset: The queryset selecting schedules, passed by django as part of the standard Action interface
    """
    rows_updated = models.ScheduleExperience.objects.filter(
        schedule__in=list(queryset)
    ).update(
        experience_type=db_name
    )
    modeladmin.message_user(request, "{} schedule(s) were changed to use the {} experience".format(rows_updated, human_name))


# Generate a list of all "set_experience_to_X" actions
experience_actions = []
for (db_name, human_name) in models.ScheduleExperience.EXPERIENCES:
    partial = functools.partial(_set_experience, db_name, human_name)
    partial.short_description = "Convert the selected schedules to the {} experience".format(human_name)
    partial.__name__ = "set_experience_to_{}".format(db_name)
    experience_actions.append(partial)


class KnownErrorCases(admin.SimpleListFilter):
    title = _('KnownErrorCases')

    parameter_name = 'error'

    def lookups(self, request, model_admin):
        return (
            ('schedule_start', _('Schedule start < course start')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'schedule_start':
            return queryset.filter(start__lt=F('enrollment__course__start'))


@admin.register(models.Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('username', 'course_id', 'active', 'start', 'upgrade_deadline', 'experience_display')
    list_display_links = ('start', 'upgrade_deadline', 'experience_display')
    list_filter = ('experience__experience_type', 'active', KnownErrorCases)
    raw_id_fields = ('enrollment',)
    readonly_fields = ('modified',)
    search_fields = ('enrollment__user__username', 'enrollment__course__id',)
    inlines = (ScheduleExperienceAdminInline,)
    actions = ['deactivate_schedules', 'activate_schedules'] + experience_actions

    def deactivate_schedules(self, request, queryset):
        rows_updated = queryset.update(active=False)
        self.message_user(request, "{} schedule(s) were deactivated".format(rows_updated))
    deactivate_schedules.short_description = "Deactivate selected schedules"

    def activate_schedules(self, request, queryset):
        rows_updated = queryset.update(active=True)
        self.message_user(request, "{} schedule(s) were activated".format(rows_updated))
    activate_schedules.short_description = "Activate selected schedules"

    def experience_display(self, obj):
        return obj.experience.get_experience_type_display()
    experience_display.short_descriptions = _('Experience')

    def username(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse("admin:auth_user_change", args=(obj.enrollment.user.id,)),
            obj.enrollment.user.username
        )

    username.allow_tags = True
    username.short_description = _('Username')

    def course_id(self, obj):
        return '<a href="{}">{}</a>'.format(
            reverse("admin:course_overviews_courseoverview_change", args=(
                obj.enrollment.course_id,
            )),
            obj.enrollment.course_id
        )

    course_id.allow_tags = True
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
