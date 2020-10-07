"""
Course Card and CourseRerunState Admin configurations
"""
from django.contrib import admin
from django.forms import ModelForm, Select

from course_action_state.models import CourseRerunState
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.features.course_card.models import CourseCard


def get_parent_courses():
    """
    Getting All Courses detail from Course Reruns

    Returns:
        tuple: A tuple includes `course_ids` along with course display name concatenated with `course_id`
    """
    course_rerun_states = CourseRerunState.objects.all()
    course_rerun_ids = [rerun.course_key for rerun in course_rerun_states]
    return tuple((co.id, "%s -- %s" % (co.display_name, co.id)) for co in CourseOverview.objects.filter(
        start__isnull=False, end__isnull=False).exclude(
        id__in=course_rerun_ids).order_by('id'))


class CardModel(ModelForm):
    """
    Model form to create/update Course Card which contains course_id and is_enabled field.
    `course_id` type (string)  id of the course.
    `is_enabled` whether to publish the course or not
    """
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
    """
    To Integrate the Card form with Django Admin.
    """
    form = CardModel


class CourseRerunStateModel(ModelForm):
    """
    Model form to create/update CourseRerun which contains source_course_key field.
    `source_course_key` is a string key which contains its `course_id` and course_title`  concatenated.
    """

    class Meta:
        model = CourseRerunState
        fields = ['source_course_key']


class CourseRerunStateModelAdmin(admin.ModelAdmin):
    """
    A model admin class to Integrate the CourseRerunState form with Django Admin.
    """
    def has_delete_permission(self, request, obj=None):
        """
        Disabling the delete permission for CourseRerunState

        Returns:
             Boolean: False, For Disabling the delete permission for CourseRerunState model admin
        """
        return False

    def get_actions(self, request):
        """
        Getting the actions except `delete_selected` action for CourseRerunState

        Returns:
            list: list of actions
        """
        actions = super(CourseRerunStateModelAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    form = CourseRerunStateModel
    list_display = ['course_key', 'source_course_key']


admin.site.register(CourseCard, CardModelAdmin)
admin.site.register(CourseRerunState, CourseRerunStateModelAdmin)
