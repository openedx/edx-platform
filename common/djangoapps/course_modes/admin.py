"""
Django admin page for course modes
"""
from django.conf import settings
from pytz import timezone, UTC
from ratelimitbackend import admin
from course_modes.models import CourseMode
from django import forms

from opaque_keys import InvalidKeyError
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from util.date_utils import get_time_display


class CourseModeForm(forms.ModelForm):

    class Meta:
        model = CourseMode

    COURSE_MODE_SLUG_CHOICES = (
        [(CourseMode.DEFAULT_MODE_SLUG, CourseMode.DEFAULT_MODE_SLUG)] +
        [(mode_slug, mode_slug) for mode_slug in CourseMode.VERIFIED_MODES] +
        [(CourseMode.NO_ID_PROFESSIONAL_MODE, CourseMode.NO_ID_PROFESSIONAL_MODE)] +
        [(mode_slug, mode_slug) for mode_slug in CourseMode.CREDIT_MODES]
    )

    mode_slug = forms.ChoiceField(choices=COURSE_MODE_SLUG_CHOICES)

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

    def __init__(self, *args, **kwargs):
        super(CourseModeForm, self).__init__(*args, **kwargs)
        if self.instance.expiration_datetime:
            default_tz = timezone(settings.TIME_ZONE)
            # django admin is using default timezone. To avoid time conversion from db to form
            # convert the UTC object to naive and then localize with default timezone.
            expiration_datetime = self.instance.expiration_datetime.replace(tzinfo=None)
            self.initial['expiration_datetime'] = default_tz.localize(expiration_datetime)

    def clean_expiration_datetime(self):
        """changing the tzinfo for a given datetime object"""
        # django admin saving the date with default timezone to avoid time conversion from form to db
        # changes its tzinfo to UTC
        if self.cleaned_data.get("expiration_datetime"):
            return self.cleaned_data.get("expiration_datetime").replace(tzinfo=UTC)


class CourseModeAdmin(admin.ModelAdmin):
    """Admin for course modes"""
    form = CourseModeForm
    search_fields = ('course_id',)
    list_display = (
        'id', 'course_id', 'mode_slug', 'mode_display_name', 'min_price',
        'currency', 'expiration_date', 'expiration_datetime_custom', 'sku'
    )
    exclude = ('suggested_prices',)

    def expiration_datetime_custom(self, obj):
        """adding custom column to show the expiry_datetime"""
        if obj.expiration_datetime:
            return get_time_display(obj.expiration_datetime, '%B %d, %Y, %H:%M  %p')

    expiration_datetime_custom.short_description = "Expiration Datetime"

admin.site.register(CourseMode, CourseModeAdmin)
