"""
These views handle all actions in Studio related to management commands
"""
import logging
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum
from opaque_keys.edx.keys import CourseKey

from edxmako.shortcuts import render_to_response
from contentstore.models import ManagementCommand
from contentstore.views.item import orphan_handler
from contentstore.management.commands.utils import get_course_versions

__all__ = [
    'dashboard',
]


log = logging.getLogger(__name__)



def get_management_commands():
    """
    Fetches all management commands.
    """
    commands = ManagementCommand.objects.all()
    return commands


# pylint: disable=unused-argument
@login_required
@ensure_csrf_cookie
@require_http_methods(("GET"))
def dashboard(request, course_key_string):
    """
    Escalate All commands dashboard.
    """
    course_usage_key = CourseKey.from_string(course_key_string)
    all_commands = get_management_commands()
    return render_to_response('management_dashboard.html', {
            'commands': all_commands
        })


# pylint: disable=unused-argument
@login_required
@require_http_methods(("GET"))
def print_draft_orphans(request, course_key_string):
    """
    Print orphans
    """
    orphan_response = orphan_handler(request, course_key_string)
    return render_to_response('management_command.html', {
            'course_key': course_key_string,
            'command_output': orphan_response.content,
            'command_name' : 'draft_orphans'
        })


# pylint: disable=unused-argument
@login_required
@require_http_methods(("GET"))
def print_published_orphans(request, course_key_string):
    """
    Print publish orphans
    """
    course_key_string = course_key_string + '+branch@published-branch'
    orphan_response = orphan_handler(request, course_key_string)
    return render_to_response('management_command.html', {
            'course_key': course_key_string,
            'command_output': orphan_response.content,
            'command_name' : 'published_orphans'
        })


# pylint: disable=unused-argument
@login_required
@require_http_methods(("GET"))
def force_publish_course(request, course_key_string):
    """
    Force publish a course
    """
    commit = True if request.GET.get('commit', False) else False
    course_key = CourseKey.from_string(course_key_string)

    if not modulestore().get_course(course_key):
        return HttpResponse("Course not found.")


    # for now only support on split mongo
    owning_store = modulestore()._get_modulestore_for_courselike(course_key)  # pylint: disable=protected-access
    if hasattr(owning_store, 'force_publish_course'):
        versions = get_course_versions(course_key_string)
        output = "Course versions : {0}".format(versions)

        if commit:
            # publish course forcefully
            updated_versions = owning_store.force_publish_course(
                course_key, ModuleStoreEnum.UserID.mgmt_command, commit
            )
            if updated_versions:
                # if publish and draft were different
                if versions['published-branch'] != versions['draft-branch']:
                    output += "\nSuccess! Published the course '{0}' forcefully.".format(course_key)
                    output += "\nUpdated course versions : \n{0}".format(updated_versions)
                else:
                    output += "\nCourse '{0}' is already in published state.".format(course_key)
            else:
                output += "\nError! Could not publish course {0}.".format(course_key)
        else:
            # if publish and draft were different
            if versions['published-branch'] != versions['draft-branch']:
                output += "\nDry run. Following would have been changed : "
                output += "\nPublished branch version {0} changed to draft branch version {1}".format(
                    versions['published-branch'], versions['draft-branch']
                )
            else:
                output += "\nDry run. Course '{0}' is already in published state.".format(course_key)
    else:
        return HttpResponse("The owning modulestore does not support this command.")

    return render_to_response('management_command.html', {
        'course_key': course_key_string,
        'command_output': output,
        'command_name': 'force_publish',
        'has_commit': True,
        'commit': commit
    })


# pylint: disable=unused-argument
@login_required
@require_http_methods(("GET"))
def export_course(request, course_key_string):
    """
    Export a course.
    """
    output = "Not implemented yet."
    return render_to_response('management_command.html', {
        'course_key': course_key_string,
        'command_output': output,
        'command_name': 'export_course'
    })


# pylint: disable=unused-argument
@login_required
@require_http_methods(("GET"))
def import_course(request, course_key_string):
    """
    Import a course.
    """
    output = "Not implemented yet."
    return render_to_response('management_command.html', {
        'course_key': course_key_string,
        'command_output': output,
        'command_name': 'import_course'
    })


# pylint: disable=unused-argument
@login_required
@require_http_methods(("GET"))
def fix_not_found(request, course_key_string):
    """
    Fix fix_not_found errors from a course.
    """
    output = "Not implemented yet."
    return render_to_response('management_command.html', {
        'course_key': course_key_string,
        'command_output': output,
        'command_name': 'fix_not_found'
    })


# pylint: disable=unused-argument
@login_required
@require_http_methods(("GET"))
def delete_orphans(request, course_key_string):
    """
    Delete orphans from a course.
    """
    commit = True if request.GET.get('commit', False) else False
    output = "Not implemented yet."
    return render_to_response('management_command.html', {
        'course_key': course_key_string,
        'command_output': output,
        'command_name': 'delete_orphans',
        'has_commit': True,
        'commit': commit
    })


# pylint: disable=unused-argument
@login_required
@require_http_methods(("GET"))
def delete_course(request, course_key_string):
    """
    Delete a course.
    """
    output = "Not implemented yet."
    return render_to_response('management_command.html', {
        'course_key': course_key_string,
        'command_output': output,
        'command_name': 'delete_course'
    })

