import json
import logging
import os

from django.views.generic import View
from django.http import HttpResponse

from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError

from student.models import CourseEnrollment
from student.auth import has_studio_write_access

from xmodule.modulestore.django import modulestore

import xblock_jupyter_graded.nbgrader_utils as nbu
from xblock_jupyter_graded.exceptions import ValidationError
from xblock_jupyter_graded.config import (
    RELEASE, SUBMITTED, SOURCE, AUTOGRADED, EDX_ROOT, FEEDBACK
)

log = logging.getLogger(__name__)


class DownloadStudentNBView(View):
    def get(self, request, course_id, unit_id, filename):
        """Serve student notebook as file download"""
        return self.get_nb(request, RELEASE, course_id, unit_id, filename)

    def get_nb(self, request, path_dir, course_id, unit_id, filename, ext=".ipynb", username=None):
        """Return proper response based on path_dir"""
        # Normalize Course/Unit id's to path values
        course = nbu.normalize_course_id(course_id)
        unit = nbu.normalize_unit_id(unit_id)
        fn_with_ext = "{}{}".format(filename, ext)

        if username:
            path = os.path.join(EDX_ROOT, course, path_dir, 
                request.user.username, unit, fn_with_ext)
        else:
            path = os.path.join(EDX_ROOT, course, path_dir, unit, fn_with_ext)

        # Validate Request and Path
        try:
            self.validate_user(request, course_id)
            self.validate_path(path, course_id, unit_id, filename)
        except ValidationError as e:
            log.info(e.msg)
            return HttpResponse(e.msg, status=e.status_code)

        # Everything good - return file
        with open(path) as f:
            response = HttpResponse(
                content=f.read()
            )
            response['content-type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename="{}.ipynb"'.format(filename)
            return response

    def validate_user(self, request, course_id):
        """Validate that course exists and user is enrolled in course"""
        try:
            course_key = CourseKey.from_string(course_id)
            c = CourseEnrollment.objects.get(user_id=request.user.id, course_id=course_key)
            if not c.is_active:
                msg = "Access Denied. {} is not currently enrolled in {}"\
                        .format(request.user.username, course_id)
                raise ValidationError(msg, 403)

        # Something wrong with CourseKey
        except InvalidKeyError as e:
            msg = "Course: {} not found".format(course_id)
            raise ValidationError(msg, 404)

        # Enrollment does not exist for user
        except CourseEnrollment.DoesNotExist:
            log.error("User: {} tried to access student notebook in: {}"\
                .format(request.user.username, course_id))
            msg = "Access Denied. Either course {} does not exist or user {} is not currently enrolled"\
                    .format(course_id, request.user.username)
            raise ValidationError(msg, 403)

    def validate_path(self, path, course_id, unit_id, filename):
        """Make sure requested path exists"""
        if not os.path.exists(path):
            msg = 'Content not found for:<br><br>course: {}<br>unit: {}<br>' \
                  'file: {}'.format(course_id, unit_id, filename)
            raise ValidationError(msg, 404)


class DownloadInstructorNBView(DownloadStudentNBView):
    def get(self, request, course_id, unit_id, filename):
        """Serve instructor notebook as file download"""
        return self.get_nb(request, SOURCE, course_id, unit_id, filename)

    def validate_user(self, request, course_id):
        """Validate user has studio access to this course"""
        try:
            course_key = CourseKey.from_string(course_id)
            if not has_studio_write_access(request.user, course_key):
                msg = "Access Denied. User: {} does not have instructor rights"\
                " in this course"\
                    .format(request.user.username)
                raise ValidationError(msg, 403)

        # Something wrong with CourseKey
        except InvalidKeyError as e:
            msg = "Course: {} not found".format(course_id)
            raise ValidationError(msg, 404)


class DownloadAutogradedNBView(DownloadStudentNBView):
    def get(self, request, course_id, unit_id, filename):
        """Serve autograded notebook as file download
        
        Denies access if instructor has not set `allow_graded_dl` to True
        """
        usage_key = UsageKey.from_string(unit_id)
        xblock = modulestore().get_item(usage_key)

        if xblock.allow_graded_dl:
            response = self.get_nb(request, FEEDBACK, course_id, unit_id, filename, 
                    ext=".html", username=request.user.username)
            response['Content-Disposition'] = 'attachment;'\
                'filename="{}_autograded.html"'.format(filename)
            return response
        else:
            msg = "Instructor has not enabled downloading of autograded notebooks"
            return HttpResponse(msg, status=403)



