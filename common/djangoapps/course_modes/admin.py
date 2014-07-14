from ratelimitbackend import admin
from course_modes.models import CourseMode
from django import forms

from opaque_keys import InvalidKeyError
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class CourseModeForm(forms.ModelForm):

    class Meta:
        model = CourseMode

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


class CourseModeAdmin(admin.ModelAdmin):
    form = CourseModeForm


admin.site.register(CourseMode, CourseModeAdmin)
