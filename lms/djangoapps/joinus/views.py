from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from courseware.courses import get_course_by_id
from edxmako.shortcuts import render_to_response

def groups(request, course_id):
    """Display the join/create/view groups view."""

    course = get_course_by_id(course_id, depth=None)

    context = {
        'course': course,
    }

    return render_to_response('groups/groups.html', context)

def join_group(request, course_id):
    """Join a group, given an invitation code."""
    course = get_course_by_id(course_id, depth=None)

    context = {
        'course': course,
    }

    return render_to_response('joinus/groups.html', context)