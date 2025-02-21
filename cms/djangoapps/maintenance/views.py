"""
Views for the maintenance app.
"""


import logging

from django.core.validators import ValidationError
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import View
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.views.generic.list import ListView
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.edxmako.shortcuts import render_to_response
from common.djangoapps.util.json_request import JsonResponse
from common.djangoapps.util.views import require_global_staff
from openedx.features.announcements.forms import AnnouncementForm
from openedx.features.announcements.models import Announcement
from xmodule.modulestore import ModuleStoreEnum  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.exceptions import ItemNotFoundError  # lint-amnesty, pylint: disable=wrong-import-order

log = logging.getLogger(__name__)

# This dict maintains all the views that will be used Maintenance app.
MAINTENANCE_VIEWS = {
    'announcement_index': {
        'url': 'maintenance:announcement_index',
        'name': _('Edit Announcements'),
        'slug': 'announcement_index',
        'description': _(
            'This view shows the announcement editor to create or alter announcements that are shown on the right'
            'side of the dashboard.'
        ),
    },
}


COURSE_KEY_ERROR_MESSAGES = {
    'empty_course_key': _('Please provide course id.'),
    'invalid_course_key': _('Invalid course key.'),
    'course_key_not_found': _('No matching course found.')
}


class MaintenanceIndexView(View):
    """
    Index view for maintenance dashboard, used by global staff.

    This view lists some commands/tasks that can be used to dry run or execute directly.
    """

    @method_decorator(require_global_staff)
    def get(self, request):
        """Render the maintenance index view. """
        return render_to_response('maintenance/index.html', {
            'views': MAINTENANCE_VIEWS,
        })


class MaintenanceBaseView(View):
    """
    Base class for Maintenance views.
    """

    template = 'maintenance/container.html'

    def __init__(self, view=None):
        super().__init__()
        self.context = {
            'view': view if view else '',
            'form_data': {},
            'error': False,
            'msg': ''
        }

    def render_response(self):
        """
        A short method to render_to_response that renders response.
        """
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(self.context)
        return render_to_response(self.template, self.context)

    @method_decorator(require_global_staff)
    def get(self, request):
        """
        Render get view.
        """
        return self.render_response()

    def validate_course_key(self, course_key, branch=ModuleStoreEnum.BranchName.draft):
        """
        Validates the course_key that would be used by maintenance app views.

        Arguments:
            course_key (string): a course key
            branch: a course locator branch, default value is ModuleStoreEnum.BranchName.draft .
                    values can be either ModuleStoreEnum.BranchName.draft or ModuleStoreEnum.BranchName.published.

        Returns:
            course_usage_key (CourseLocator): course usage locator
        """
        if not course_key:
            raise ValidationError(COURSE_KEY_ERROR_MESSAGES['empty_course_key'])

        course_usage_key = CourseKey.from_string(course_key)

        if not modulestore().has_course(course_usage_key):
            raise ItemNotFoundError(COURSE_KEY_ERROR_MESSAGES['course_key_not_found'])

        # get branch specific locator
        course_usage_key = course_usage_key.for_branch(branch)

        return course_usage_key


class AnnouncementBaseView(View):
    """
    Base view for Announcements pages
    """

    @method_decorator(require_global_staff)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class AnnouncementIndexView(ListView, MaintenanceBaseView):
    """
    View for viewing the announcements shown on the dashboard, used by the global staff.
    """
    model = Announcement
    object_list = Announcement.objects.order_by('-active')
    context_object_name = 'announcement_list'
    paginate_by = 8

    def __init__(self):
        super().__init__(MAINTENANCE_VIEWS['announcement_index'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['view'] = MAINTENANCE_VIEWS['announcement_index']
        return context

    @method_decorator(require_global_staff)
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        return render_to_response(self.template, context)


class AnnouncementEditView(UpdateView, AnnouncementBaseView):
    """
    View for editing an announcement.
    """
    model = Announcement
    form_class = AnnouncementForm
    success_url = reverse_lazy('maintenance:announcement_index')
    template_name = '/maintenance/_announcement_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_url'] = reverse('maintenance:announcement_edit', kwargs={'pk': context['announcement'].pk})
        return context


class AnnouncementCreateView(CreateView, AnnouncementBaseView):
    """
    View for creating an announcement.
    """
    model = Announcement
    form_class = AnnouncementForm
    success_url = reverse_lazy('maintenance:announcement_index')
    template_name = '/maintenance/_announcement_edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_url'] = reverse('maintenance:announcement_create')
        return context


class AnnouncementDeleteView(DeleteView, AnnouncementBaseView):
    """
    View for deleting an announcement.
    """
    model = Announcement
    success_url = reverse_lazy('maintenance:announcement_index')
    template_name = '/maintenance/_announcement_delete.html'
