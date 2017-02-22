"""
Views for the maintenance app.
"""
import logging
from django.db import transaction
from django.core.validators import ValidationError
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import View

from edxmako.shortcuts import render_to_response
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

from contentstore.management.commands.utils import get_course_versions
from util.json_request import JsonResponse
from util.views import require_global_staff


log = logging.getLogger(__name__)

# This dict maintains all the views that will be used Maintenance app.
MAINTENANCE_VIEWS = {
    'force_publish_course': {
        'url': 'maintenance:force_publish_course',
        'name': _('Force Publish Course'),
        'slug': 'force_publish_course',
        'description': _(
            'Sometimes the draft and published branches of a course can get out of sync. Force publish course command '
            'resets the published branch of a course to point to the draft branch, effectively force publishing the '
            'course. This view dry runs the force publish command'
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
        if self.request.is_ajax():
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


class ForcePublishCourseView(MaintenanceBaseView):
    """
    View for force publishing state of the course, used by the global staff.

    This view uses `force_publish_course` method of modulestore which publishes the draft state of the course. After
    the course has been forced published, both draft and publish draft point to same location.
    """

    def __init__(self):
        super(ForcePublishCourseView, self).__init__(MAINTENANCE_VIEWS['force_publish_course'])
        self.context.update({
            'current_versions': [],
            'updated_versions': [],
            'form_data': {
                'course_id': '',
                'is_dry_run': True
            }
        })

    def get_course_branch_versions(self, versions):
        """
        Returns a dict containing unicoded values of draft and published draft versions.
        """
        return {
            'draft-branch': unicode(versions['draft-branch']),
            'published-branch': unicode(versions['published-branch'])
        }

    @transaction.atomic
    @method_decorator(require_global_staff)
    def post(self, request):
        """
        This method force publishes a course if dry-run argument is not selected. If dry-run is selected, this view
        shows possible outcome if the `force_publish_course` modulestore method is executed.

        Arguments:
            course_id (string): a request parameter containing course id
            is_dry_run (string): a request parameter containing dry run value.
                                 It is obtained from checkbox so it has either values 'on' or ''.
        """
        course_id = request.POST.get('course-id')

        self.context.update({
            'form_data': {
                'course_id': course_id
            }
        })

        try:
            course_usage_key = self.validate_course_key(course_id)
        except InvalidKeyError:
            self.context['error'] = True
            self.context['msg'] = COURSE_KEY_ERROR_MESSAGES['invalid_course_key']
        except ItemNotFoundError as exc:
            self.context['error'] = True
            self.context['msg'] = exc.message
        except ValidationError as exc:
            self.context['error'] = True
            self.context['msg'] = exc.message

        if self.context['error']:
            return self.render_response()

        source_store = modulestore()._get_modulestore_for_courselike(course_usage_key)  # pylint: disable=protected-access
        if not hasattr(source_store, 'force_publish_course'):
            self.context['msg'] = _('Force publishing course is not supported with old mongo courses.')
            log.warning(
                'Force publishing course is not supported with old mongo courses. \
                %s attempted to force publish the course %s.',
                request.user,
                course_id,
                exc_info=True
            )
            return self.render_response()

        current_versions = self.get_course_branch_versions(get_course_versions(course_id))

        # if publish and draft are NOT different
        if current_versions['published-branch'] == current_versions['draft-branch']:
            self.context['msg'] = _('Course is already in published state.')
            log.warning(
                'Course is already in published state. %s attempted to force publish the course %s.',
                request.user,
                course_id,
                exc_info=True
            )
            return self.render_response()

        self.context['current_versions'] = current_versions
        log.info(
            '%s dry ran force publish the course %s.',
            request.user,
            course_id,
            exc_info=True
        )
        return self.render_response()
