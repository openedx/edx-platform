# -*- coding:utf-8 -*-
from __future__ import unicode_literals
from django import forms
from django.http.request import QueryDict
from opaque_keys.edx.keys import CourseKey
from django.contrib import admin
from professors.models import Professor, ProfessorCourses


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):

    search_fields = ('name',)

    list_display = (
        'id',
        'user',
        'name',
        'description',
        'is_active',
        'sort_num'
    )


class ProfessorCoursesForm(forms.ModelForm):
    """
    Admin form for adding a course mode.
    """

    class Meta(object):
        model = ProfessorCourses
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        """
        If args is a QueryDict, then the ModelForm addition request came in as a POST with a course ID string.
        # Change the course ID string to a CourseLocator object by copying the QueryDict to make it mutable.
        :param args:
        :param kwargs:
        """
        if len(args) > 0 and 'course' in args[0] and isinstance(args[0], QueryDict):
            args_copy = args[0].copy()
            args_copy['course'] = CourseKey.from_string(args_copy['course'])
            args = [args_copy]

        super(ProfessorCoursesForm, self).__init__(*args, **kwargs)

        try:
            if self.data.get('course'):
                self.data['course'] = CourseKey.from_string(self.data['course'])
        except AttributeError:
            # Change the course ID string to a CourseLocator.
            # On a POST request, self.data is a QueryDict and is immutable - so this code will fail.
            # However, the args copy above before the super() call handles this case.
            pass

    def save(self, commit=True):
        """
        Save the form data.
        """
        # Trigger validation so we can access cleaned data

        return super(ProfessorCoursesForm, self).save(commit=commit)


@admin.register(ProfessorCourses)
class ProfessorCoursesAdmin(admin.ModelAdmin):

    form = ProfessorCoursesForm

    list_display = (
        'id',
        'professor',
        'course',
        'is_active',
        'sort_num'
    )
