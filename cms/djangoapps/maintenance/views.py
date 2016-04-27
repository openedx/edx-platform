"""
Views for the maintenance app.
"""
from django.core.urlresolvers import reverse_lazy
from django.http import Http404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from edxmako.shortcuts import render_to_response
from util.course_key_utils import course_key_from_string_or_404
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from util.views import require_global_staff


MAINTENANCE_COMMANDS = {
    "show_orphans": {
        "url": reverse_lazy("maintenance:show_orphans"),
        "name": _("Print Orphans"),
        "slug": "show_orphans",
        "description": _("View orphans."),
    },
    "delete_orphans": {
        "url": reverse_lazy("maintenance:delete_orphans"),
        "name": _("Delete Orphans"),
        "slug": "delete_orphans",
        "description": _("Delete orphans."),
    },
    "export_course": {
        "url": reverse_lazy("maintenance:export_course"),
        "name": _("Export Course"),
        "slug": "export_course",
        "description": _("Export course"),
    },
    "import_course": {
        "url": reverse_lazy("maintenance:import_course"),
        "name": _("Import Course"),
        "slug": "import_course",
        "description": _("Import Course."),
    },
    "delete_course": {
        "url": reverse_lazy("maintenance:delete_course"),
        "name": _("Delete Course"),
        "slug": "delete_course",
        "description": _("Delete course."),
    },
    "force_publish_course": {
        "url": reverse_lazy("maintenance:force_publish_course"),
        "name": _("Force Publish Course"),
        "slug": "force_publish_course",
        "description": _("Force publish course."),
    },
}


class MaintenanceIndexView(View):
    """
    View for maintenance dashboard, used by the escalation team.
    """

    @method_decorator(require_global_staff)
    def get(self, request):
        """Render the maintenance index view. """
        return render_to_response('maintenance/index.html', {
            "commands": MAINTENANCE_COMMANDS,
        })


class ShowOrphansView(View):
    """
    View for viewing course orphans, used by the escalation team.
    """

    def get_orphans(self, course_id, branch=False):
        """Get orphans for a course"""
        if branch == 'published':
            course_id += "+branch@published-branch"
        course_usage_key = course_key_from_string_or_404(course_id)
        orphans = modulestore().get_orphans(course_usage_key)
        return orphans

    @method_decorator(require_global_staff)
    def get(self, request):
        """Render show orphans view """
        return render_to_response('maintenance/container.html', {
            'command': MAINTENANCE_COMMANDS['show_orphans'],
        })

    @method_decorator(require_global_staff)
    def post(self, request):
        """ Process and return course orphans"""
        course_id = request.POST.get('course-id')
        branch = request.POST.get('draft-published-branch', 'draft')
        orphans = []
        context = {
            'command': MAINTENANCE_COMMANDS['show_orphans'],
            'error': False,
            'msg': '',
            'success': True,
            'orphans': orphans,
            'form_data': {
                'course_id': course_id,
                'branch': branch
            },
        }
        if course_id:
            try:
                orphans = self.get_orphans(course_id, branch)
                if orphans:
                    context['orphans'] = orphans
                else:
                    context['msg'] = "No orphans found."
            except Http404:
                context['success'] = False
                context['error'] = True
                context['msg'] = "Invalid course key."
            except ItemNotFoundError:
                context['success'] = False
                context['error'] = True
                context['msg'] = "No matching course found."
        else:
            context['success'] = False
            context['error'] = True
            context['msg'] = "Please provide course id."
        return render_to_response('maintenance/container.html', context)


class DeleteOrphansView(View):
    """
    View for deleting course orphans, used by the escalation team.
    """

    @method_decorator(require_global_staff)
    def get(self, request):
        """Render delete orphans view """
        return render_to_response('maintenance/container.html', {
            'command': MAINTENANCE_COMMANDS['delete_orphans'],
        })


class DeleteCourseView(View):
    """
    View for deleting a course orphans, used by the escalation team.
    """

    @method_decorator(require_global_staff)
    def get(self, request):
        """Render delete course view """
        return render_to_response('maintenance/container.html', {
            'command': MAINTENANCE_COMMANDS['delete_course'],
        })


class ExportCourseView(View):
    """
    View for exporting course, used by the escalation team.
    """

    @method_decorator(require_global_staff)
    def get(self, request):
        """Render export course view """
        return render_to_response('maintenance/container.html', {
            'command': MAINTENANCE_COMMANDS['export_course'],
        })


class ImportCourseView(View):
    """
    View for importing course orphans, used by the escalation team.
    """

    @method_decorator(require_global_staff)
    def get(self, request):
        """Render import course view """
        return render_to_response('maintenance/container.html', {
            'command': MAINTENANCE_COMMANDS['import_course'],
        })


class ForcePublishCourseView(View):
    """
    View for force publish state of the course, used by the escalation team.
    """

    @method_decorator(require_global_staff)
    def get(self, request):
        """Render force publish course view """
        return render_to_response('maintenance/container.html', {
            'command': MAINTENANCE_COMMANDS['force_publish_course'],
        })
