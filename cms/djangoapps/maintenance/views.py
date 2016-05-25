"""
Views for the maintenance app.
"""
import logging
from django.db import transaction
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View

from edxmako.shortcuts import render_to_response
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from contentstore.management.commands.utils import get_course_versions
from util.views import require_global_staff


log = logging.getLogger(__name__)

MAINTENANCE_COMMANDS = {
    "show_orphans": {
        "url": reverse_lazy("maintenance:show_orphans"),
        "name": _("Print Orphans"),
        "slug": "show_orphans",
        "description": _("View orphans."),
    },
    "force_publish_course": {
        "url": reverse_lazy("maintenance:force_publish_course"),
        "name": _("Force Publish Course"),
        "slug": "force_publish_course",
        "description": _("Force publish course."),
    },
}


COURSE_KEY_ERROR_MESSAGES = {
    'empty_course_key': _('Please provide course id.'),
    'invalid_course_key': _('Invalid course key.'),
    'course_key_not_found': _('No matching course found.')
}


def get_maintenace_urls():
    url_list = []
    for key, val in MAINTENANCE_COMMANDS.items():
        url_list.append(val['url'])
    return url_list 


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


class MaintenanceBaseView(View):

    template = 'maintenance/container.html'

    def __init__(self, command=None):
        self.context = {
            'command': command if command else '',
            'form_data': {},
            'error': False,
            'msg': ''
        }

    def render_response(self):
        return render_to_response(self.template, self.context)

    @method_decorator(require_global_staff)
    def get(self, request):
        """Render get view."""
        return self.render_response()

    def validate_course_key(self, course_key, branch=None):
        """Validates course_key and updates context, returns usage_key, that would be used by maintenance app views."""
        course_usage_key = None
        if not course_key:
            self.context['error'] = True
            self.context['msg'] = COURSE_KEY_ERROR_MESSAGES['empty_course_key']
            return course_usage_key
        try:
            if branch == "published":
                course_key += "+branch@published-branch"

            course_usage_key = CourseKey.from_string(course_key)
            if not modulestore().has_course(course_usage_key):
                raise ItemNotFoundError

            self.context.update({
                'error': False,
                'msg': ''
            })
        except InvalidKeyError:
            self.context['error'] = True
            self.context['msg'] = COURSE_KEY_ERROR_MESSAGES['invalid_course_key']
        except ItemNotFoundError:
            self.context['error'] = True
            self.context['msg'] = COURSE_KEY_ERROR_MESSAGES['course_key_not_found']
        return course_usage_key


class ForcePublishCourseView(MaintenanceBaseView):
    """
    View for force publish state of the course, used by the escalation team.
    """

    def __init__(self):
        super(ForcePublishCourseView, self).__init__(MAINTENANCE_COMMANDS['force_publish_course'])
        self.context.update({
            'current_versions': [],
            'updated_versions': [],
            'form_data': {
                'course_id': '',
                'is_dry_run': True
            }
        })

    @transaction.atomic
    @method_decorator(require_global_staff)
    def post(self, request):
        """Force publish a course."""

        course_id = request.POST.get('course-id')
        is_dry_run = bool(request.POST.get('dry-run'))

        course_usage_key = self.validate_course_key(course_id)

        self.context.update({
            'form_data': {
                'course_id': course_id,
                'is_dry_run': is_dry_run
            }
        })

        if self.context['error']:
            return self.render_response()

        owning_store = modulestore()._get_modulestore_for_courselike(course_usage_key)  # pylint: disable=protected-access
        if not hasattr(owning_store, 'force_publish_course'):
            msg = "Force publish course does not support old mongo style courses."
            self.context['msg'] = _(msg)
            logging.info(
                "%s %s attempted to force publish the course %s.",
                msg,
                request.user,
                course_id,
                exc_info=True
            )
            return self.render_response()

        current_versions = get_course_versions(course_id)

        # if publish and draft were different
        if current_versions['published-branch'] == current_versions['draft-branch']:
            msg = "Course is already in published state."
            self.context['msg'] = _(msg)
            logging.info(
                "%s %s attempted to force publish the course %s.",
                msg,
                request.user,
                course_id,
                exc_info=True
            )
            return self.render_response()

        self.context['current_versions'] = current_versions

        if is_dry_run:
            logging.info(
                "%s dry ran force publish the course %s.",
                request.user,
                course_id,
                exc_info=True
            )
            return self.render_response()

        updated_versions = owning_store.force_publish_course(
            course_usage_key, request.user, commit=True
        )
        if not updated_versions:
            msg = "Could not publish course."
            self.context['msg'] = _(msg)
            logging.info(
                "%s %s attempted to force publish the course %s.",
                request.user,
                course_id,
                exc_info=True
            )
            return self.render_response()

        self.context['updated_versions'] = updated_versions
        msg = "Published branch version changed from {published_prev} to {published_new}.".format(
            published_prev=current_versions['published-branch'],
            published_new=updated_versions['published-branch']
        )
        logging.info(
            "%s %s published course %s forcefully.",
            msg,
            request.user,
            course_id,
            exc_info=True
        )
        return self.render_response()


class ShowOrphansView(MaintenanceBaseView):
    """
    View for viewing course orphans, used by the escalation team.
    """

    def __init__(self):
        super(ShowOrphansView, self).__init__(MAINTENANCE_COMMANDS['show_orphans'])
        self.context.update({
            'orphans': [],
            'form_data': {
                'course_id': '',
                'branch': 'draft'
            }
        })

    @method_decorator(require_global_staff)
    def post(self, request):
        """Process and return course orphans."""
        course_id = request.POST.get('course-id')
        branch = request.POST.get('draft-published-branch', 'draft')

        course_usage_key = self.validate_course_key(course_id, branch)

        self.context.update({
            'form_data': {
                'course_id': course_id,
                'branch': branch
            },
        })

        if self.context['error']:
            return self.render_response()

        orphans = modulestore().get_orphans(course_usage_key)
        if not orphans:
            msg = "No orphans found."
            self.context['msg'] = _(msg)
            logging.info(
                "%s %s tried to find %s branch orphans for course %s.",
                msg,
                request.user,
                branch,
                course_id,
                exc_info=True
            )
            self.render_response()

        self.context['orphans'] = orphans
        logging.info(
            "%s found %s branch orphans for course %s.",
            request.user,
            branch,
            course_id,
            exc_info=True
        )
        return self.render_response()
