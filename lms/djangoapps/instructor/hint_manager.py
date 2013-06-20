'''
Views for hint management.
'''

from collections import defaultdict
import csv
import json
import logging
from markupsafe import escape
import os
import re
import requests
from requests.status_codes import codes
import urllib
from collections import OrderedDict

from StringIO import StringIO

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.http import HttpResponse, Http404
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.cache import cache_control
from mitxmako.shortcuts import render_to_response, render_to_string
from django.core.urlresolvers import reverse

from courseware.courses import get_course_with_access
from courseware.models import XModuleContentField


@ensure_csrf_cookie
def hint_manager(request, course_id):
    try:
        course = get_course_with_access(request.user, course_id, 'staff', depth=None)
    except Http404:
        out = 'Sorry, but students are not allowed to access the hint manager!'
        return
    if request.method == 'GET':
        out = get_hints(request, course_id, 'mod_queue')
        return render_to_response('courseware/hint_manager.html', out)
    field = request.POST['field']
    if not (field == 'mod_queue' or field == 'hints'):
        # Invalid field.  (Don't let users continue - they may overwrite other db's)
        return 
    if request.POST['op'] == 'delete hints':
        delete_hints(request, course_id, field)
    if request.POST['op'] == 'switch fields':
        pass
    if request.POST['op'] == 'change votes':
        change_votes(request, course_id, field)
    rendered_html = render_to_string('courseware/hint_manager_inner.html', get_hints(request, course_id, field))
    return HttpResponse(json.dumps({'success': True, 'contents': rendered_html}))



def get_hints(request, course_id, field):
    # field indicates the database entry that we are modifying.
    # Right now, the options are 'hints' or 'mod_queue'.
    # DON'T TRUST field attributes that come from ajax.  Use an if statement
    # to make sure the field is valid before plugging into functions.

    out = ''
    if field == 'mod_queue':
        other_field = 'hints'
        field_label = 'Hints Awaiting Moderation'
        other_field_label = 'Approved Hints'
    elif field == 'hints':
        other_field = 'mod_queue'
        field_label = 'Approved Hints'
        other_field_label = 'Hints Awaiting Moderation'
    chopped_id = '/'.join(course_id.split('/')[:-1])
    chopped_id = re.escape(chopped_id)
    all_hints = XModuleContentField.objects.filter(field_name=field, definition_id__regex=chopped_id)
    for problem in all_hints:
        out += '<h2> Problem: ' + problem.definition_id + '</h2>'
        for answer, hint_dict in json.loads(problem.value).items():
            out += '<h4> Answer: ' + answer + '</h4>'
            for pk, hint in hint_dict.items():
                out += '<p data-problem="'\
                    + problem.definition_id + '" data-pk="' + str(pk) + '" data-answer="'\
                    + answer + '">'
                out += '<input class="hint-select" type="checkbox"/>' + hint[0] + \
                    '<br /> Votes: <input type="text" class="votes" value="' + str(hint[1]) + '"></input>'
                out += '</p>'
        out += '''<h4> Add a hint to this problem </h4>
            Answer (exact formatting):
            <input type="text" id="new-hint-answer-''' + problem.definition_id \
            + '"/> <br /> Hint: <br /><textarea cols="50" style="height:200px" id="new-hint-' + problem.definition_id \
            + '"></textarea> <br /> <button class="submit-new-hint" data-problem="' + problem.definition_id \
            + '"> Submit </button><br />'


    out += '<button id="hint-delete"> Delete selected </button> <button id="update-votes"> Update votes </button>'
    render_dict = {'out': out,
                   'field': field,
                   'other_field': other_field,
                   'field_label': field_label,
                   'other_field_label': other_field_label,
                   'all_hints': all_hints}
    return render_dict

def delete_hints(request, course_id, field):
    '''
    Deletes the hints specified by the [problem_defn_id, answer, pk] tuples in the numbered
    fields of request.POST.
    '''
    for key in request.POST:
        if key == 'op' or key == 'field':
            continue
        problem_id, answer, pk = request.POST.getlist(key)
        # Can be optimized - sort the delete list by problem_id, and load each problem
        # from the database only once.
        this_problem = XModuleContentField.objects.get(field_name=field, definition_id=problem_id)
        problem_dict = json.loads(this_problem.value)
        del problem_dict[answer][pk]
        this_problem.value = json.dumps(problem_dict)
        this_problem.save()

def change_votes(request, course_id, field):
    '''
    Updates the number of votes.  The numbered fields of request.POST contain
    [problem_id, answer, pk, new_votes] tuples.
    - Very similar to delete_hints.  Is there a way to merge them?  Nah, too complicated.
    '''
    for key in request.POST:
        if key == 'op' or key == 'field':
            continue
        problem_id, answer, pk, new_votes = request.POST.getlist(key)
        this_problem = XModuleContentField.objects.get(field_name=field, definition_id=problem_id)
        problem_dict = json.loads(this_problem.value)
        problem_dict[answer][pk][1] = new_votes
        this_problem.value = json.dumps(problem_dict)
        this_problem.save()





