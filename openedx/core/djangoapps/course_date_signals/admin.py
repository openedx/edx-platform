"""
Django Admin pages for SelfPacedRelativeDatesConfig.
"""
from dal import autocomplete

from django import forms
from django.contrib import admin
from django.urls import path

from xmodule.modulestore.django import modulestore
from openedx.core.djangoapps.config_model_utils.admin import StackedConfigModelAdmin
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from .models import SelfPacedRelativeDatesConfig


class CourseInOrgAutocomplete(autocomplete.Select2ListView):
    def get_list(self):
        course_names = [
            SelfPacedRelativeDatesConfig._org_course_from_course_key(c.id)
            for c in modulestore().get_courses()
        ]
        if self.q:
            return [name for name in course_names if self.q.lower() in name.lower()]
        return course_names


class CourseIDAutocomplete(autocomplete.Select2ListView):
    def get_list(self):
        ids = [str(course.id) for course in modulestore().get_courses()]
        if self.q:
            return [cid for cid in ids if self.q.lower() in cid.lower()]
        return ids


class SelfPacedRelativeDatesConfigForm(forms.ModelForm):
    ORG_CHOICES = sorted(set((c.org, c.org) for c in modulestore().get_courses()))

    org = forms.ChoiceField(
        choices=[('', '---------')] + ORG_CHOICES,
        required=False
    )

    org_course = forms.MultipleChoiceField(
        required=False,
        widget=autocomplete.Select2Multiple(
            url='admin:course-in-org-autocomplete',
            attrs={
                'data-tags': 'true',
                'multiple': 'multiple',
            }
        )
    )

    course = forms.ModelChoiceField(
        required=False,
        queryset=CourseOverview.objects.all(),
        widget=autocomplete.ModelSelect2(
            url='admin:course-id-autocomplete',
            attrs={
                'data-placeholder': 'Select a course run…',
                'data-allow-clear': 'true',
            }
        )
    )

    class Meta:
        model = SelfPacedRelativeDatesConfig
        fields = '__all__'

    def clean(self):
        cleaned = super().clean()

        values = self.data.getlist('org_course')
        cleaned['org_course'] = ','.join(values)

        return cleaned


@admin.register(SelfPacedRelativeDatesConfig)
class SelfPacedRelativeDatesAdmin(StackedConfigModelAdmin):
    form = SelfPacedRelativeDatesConfigForm

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'course-in-org-autocomplete/',
                CourseInOrgAutocomplete.as_view(),
                name='course-in-org-autocomplete'
            ),
            path(
                'course-id-autocomplete/',
                CourseIDAutocomplete.as_view(),
                name='course-id-autocomplete'
            ),
        ]
        return custom_urls + urls
