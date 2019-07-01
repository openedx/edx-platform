# -*- coding:utf-8 -*-
from django.contrib import admin
from django import forms
from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from django.core.exceptions import ValidationError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from django.core.validators import URLValidator

from .models import MainClassification,FirstClassification,SecondClassification,ThirdClassification,CourseClassification

class MainClassificationAdminForm(forms.ModelForm):
    class Meta(object):
        model = MainClassification
        fields = '__all__'

class MainClassificationAdmin(admin.ModelAdmin):
    form = MainClassificationAdminForm
    fields = ('sequence','name','show_opt')
    list_display = ('name','sequence','show_opt',)

#########################################################

class FirstClassificationAdminForm(forms.ModelForm):
    class Meta(object):
        model = FirstClassification
        fields = '__all__'

class FirstClassificationAdmin(admin.ModelAdmin):
    form = FirstClassificationAdminForm
    fields = ('name',)
    list_display = ('name',)
#########################################################

class SecondClassificationAdminForm(forms.ModelForm):
    class Meta(object):
        model = SecondClassification
        fields = '__all__'

class SecondClassificationAdmin(admin.ModelAdmin):
    form = SecondClassificationAdminForm
    fields = ('name',)
    list_display = ('name',)
#########################################################

class ThirdClassificationAdminForm(forms.ModelForm):
    class Meta(object):
        model = ThirdClassification
        fields = '__all__'

class ThirdClassificationAdmin(admin.ModelAdmin):
    form = ThirdClassificationAdminForm
    fields = ('name',)
    list_display = ('name',)
#########################################################

class CourseClassificationAdminForm(forms.ModelForm):
    class Meta(object):
        model = CourseClassification
        fields = '__all__'

    def clean_course_id(self):
        course_id = self.cleaned_data['course_id']
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            try:
                course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
            except InvalidKeyError:
                raise forms.ValidationError("Cannot make a valid CourseKey from id {}!".format(course_id))

        if not modulestore().has_course(course_key):
            raise forms.ValidationError("Cannot find course with id {} in the modulestore".format(course_id))

        return course_key

    def save(self,commit=True):
        return super(CourseClassificationAdminForm,self).save(commit=commit)

class CourseClassificationAdmin(admin.ModelAdmin):
    form = CourseClassificationAdminForm
    fields = ('course_id','MainClass','FirstClass','SecondClass','ThirdClass')
    search_fields = ('course_id',)
    list_display = ('course_id','MainClass','FirstClass','SecondClass','ThirdClass')

admin.site.register(MainClassification,MainClassificationAdmin)
admin.site.register(FirstClassification,FirstClassificationAdmin)
admin.site.register(SecondClassification,SecondClassificationAdmin)
admin.site.register(ThirdClassification,ThirdClassificationAdmin)
admin.site.register(CourseClassification,CourseClassificationAdmin)


