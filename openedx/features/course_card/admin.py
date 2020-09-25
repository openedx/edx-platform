from django.contrib import admin
from django.forms import ModelForm, Select

from course_action_state.models import CourseRerunState
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.course_card.models import CourseCard


def get_parent_courses():
    course_rerun_states = CourseRerunState.objects.all()
    course_rerun_ids = [rerun.course_key for rerun in course_rerun_states]
    return tuple((co.id, "%s -- %s" % (co.display_name, co.id)) for co in CourseOverview.objects.filter(
        start__isnull=False, end__isnull=False).exclude(
        id__in=course_rerun_ids).order_by('id'))


class CardModel(ModelForm):
    def __init__(self, *args, **kwargs):
        """
        Only show parent courses in admin site to create cards
        :param args:
        :param kwargs:
        """
        super(CardModel, self).__init__(*args, **kwargs)

        self.fields['course_id'].widget = \
            Select(choices=get_parent_courses())

    class Meta:
        model = CourseCard
        fields = ['course_id', 'is_enabled']


class CardModelAdmin(admin.ModelAdmin):
    form = CardModel


class CourseRerunStateModel(ModelForm):
    def __init__(self, *args, **kwargs):

        super(CourseRerunStateModel, self).__init__(*args, **kwargs)

    class Meta:
        model = CourseRerunState
        fields = ['source_course_key']


class CourseRerunStateModelAdmin(admin.ModelAdmin):

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super(CourseRerunStateModelAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    form = CourseRerunStateModel
    list_display = ['course_key', 'source_course_key']


admin.site.register(CourseCard, CardModelAdmin)
admin.site.register(CourseRerunState, CourseRerunStateModelAdmin)
