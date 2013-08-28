"""
Views for hint management.

Get to these views through courseurl/hint_manager.
For example: https://courses.edx.org/courses/MITx/2.01x/2013_Spring/hint_manager

These views will only be visible if MITX_FEATURES['ENABLE_HINTER_INSTRUCTOR_VIEW'] = True
"""

import json
import copy

from django.http import HttpResponse, Http404
from django_future.csrf import ensure_csrf_cookie
from django.utils.translation import ugettext as _

from mitxmako.shortcuts import render_to_response, render_to_string

from courseware.courses import get_course_with_access
from courseware.models import XModuleContentField
import courseware.module_render as module_render
import courseware.model_data as model_data
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore


@ensure_csrf_cookie
def hint_manager(request, course_id):
    """
    The URL landing function for all calls to the hint manager, both POST and GET.
    """
    try:
        get_course_with_access(request.user, course_id, 'staff', depth=None)
    except Http404:
        out = _('Sorry, but students are not allowed to access the hint manager!')
        return HttpResponse(out)
    if request.method == 'GET':
        out = get_hints(request, course_id, 'mod_queue')
        out.update({'error': ''})
        return render_to_response('instructor/hint_manager.html', out)
    field = request.POST['field']
    if not (field == 'mod_queue' or field == 'hints'):
        # Invalid field.  (Don't let users continue - they may overwrite other db's)
        out = _('Error in hint manager - an invalid field was accessed.')
        return HttpResponse(out)

    switch_dict = {
        'delete hints': delete_hints,
        'switch fields': lambda *args: None,    # Takes any number of arguments, returns None.
        'change votes': change_votes,
        'add hint': add_hint,
        'approve': approve,
    }

    # Do the operation requested, and collect any error messages.
    error_text = switch_dict[request.POST['op']](request, course_id, field)
    if error_text is None:
        error_text = ''
    render_dict = get_hints(request, course_id, field)
    render_dict.update({'error': error_text})
    rendered_html = render_to_string('instructor/hint_manager_inner.html', render_dict)
    return HttpResponse(json.dumps({'success': True, 'contents': rendered_html}))


def get_hints(request, course_id, field):
    """
    Load all of the hints submitted to the course.

    Args:
    `request` -- Django request object.
    `course_id` -- The course id, like 'Me/19.002/test_course'
    `field` -- Either 'hints' or 'mod_queue'; specifies which set of hints to load.

    Keys in returned dict:
        - 'field': Same as input
        - 'other_field': 'mod_queue' if `field` == 'hints'; and vice-versa.
        - 'field_label', 'other_field_label': English name for the above.
        - 'all_hints': A list of [answer, pk dict] pairs, representing all hints.
          Sorted by answer.
        - 'id_to_name': A dictionary mapping problem id to problem name.

    Someone may want to separate this by problem in the future.
    """
    if field == 'mod_queue':
        other_field = 'hints'
        field_label = _('Hints Awaiting Moderation')
        other_field_label = _('Approved Hints')
    elif field == 'hints':
        other_field = 'mod_queue'
        field_label = _('Approved Hints')
        other_field_label = _('Hints Awaiting Moderation')
    # big_out_dict[problem id] = [[answer, {pk: [hint, votes]}], sorted by answer]
    # big_out_dict maps a problem id to a list of [answer, hints] pairs, sorted in order of answer.
    big_out_dict = {}
    # id_to name maps a problem id to the name of the problem.
    # id_to_name[problem id] = Display name of problem
    id_to_name = {}

    # Get all of the hinters in this course.
    org, course_number, course_name = course_id.split('/')
    hinter_filter = Location('i4x', org, course_number, 'crowdsource_hinter', None)
    hinters = modulestore().get_items(hinter_filter, course_id=course_id)
    model_data_cache = model_data.ModelDataCache(hinters, course_id, request.user)

    def answer_sorter(thing):
        """
        `thing` is a tuple, where `thing[0]` contains an answer, and `thing[1]` contains
        a dict of hints.  This function returns an index based on `thing[0]`, which
        is used as a key to sort the list of things.
        """
        try:
            return float(thing[0])
        except ValueError:
            # Put all non-numerical answers first.
            return float('-inf')

    # For each hinter, get and process a list of all hints.
    for hinter_descriptor in hinters:
        hinter_module = module_render.get_module(
            request.user,
            request,
            hinter_descriptor.location,
            model_data_cache,
            course_id
        )
        loc_string = str(hinter_descriptor.location)
        # To code reviewers: Do you think this is OK?  I make sure that field
        # can only be 'hints' or 'mod_queue' earlier.
        hints = getattr(hinter_module, field)
        big_out_dict[loc_string] = sorted(hints.items(), key=answer_sorter)

        # Also generate the name of the problem to which this hinter is pointed.
        problem_descriptor = modulestore().get_items(hinter_module.target_problem, course_id=course_id)[0]
        id_to_name[loc_string] = problem_descriptor.display_name_with_default

    render_dict = {'field': field,
                   'other_field': other_field,
                   'field_label': field_label,
                   'other_field_label': other_field_label,
                   'all_hints': big_out_dict,
                   'id_to_name': id_to_name}
    return render_dict


def _location_to_module(location, request, course_id):
    """
    Converts a location string to a module.  Requires the request and course_id
    objects.
    """
    loc = Location(location)
    descriptor = modulestore().get_items(loc, course_id=course_id)[0]
    model_data_cache = model_data.ModelDataCache([descriptor], course_id, request.user)
    return module_render.get_module(
        request.user,
        request,
        loc,
        model_data_cache,
        course_id
    )


def delete_hints(request, course_id, field):
    """
    Deletes the hints specified.

    `request.POST` contains some fields keyed by integers.  Each such field contains a
    [problem_defn_id, answer, pk] tuple.  These tuples specify the hints to be deleted.

    Example `request.POST`:
    {'op': 'delete_hints',
     'field': 'mod_queue',
      1: ['problem_whatever', '42.0', '3'],
      2: ['problem_whatever', '32.5', '12']}
    """
    for key in request.POST:
        if key == 'op' or key == 'field':
            continue
        problem_id, answer, pk = request.POST.getlist(key)
        # Can be optimized - sort the delete list by problem_id, and load each problem
        # from the database only once.
        hinter_module = _location_to_module(problem_id, request, course_id)
        try:
            del getattr(hinter_module, field)[answer][pk]
        except KeyError:
            return 'No hint found to delete!'
        # Remember to save after modifying an xmodule!
        hinter_module.save()


def change_votes(request, course_id, field):
    """
    Updates the number of votes.

    The numbered fields of `request.POST` contain [problem_id, answer, pk, new_votes] tuples.
    See `delete_hints`.

    Example `request.POST`:
    {'op': 'delete_hints',
     'field': 'mod_queue',
      1: ['problem_whatever', '42.0', '3', 42],
      2: ['problem_whatever', '32.5', '12', 9001]}
    """

    for key in request.POST:
        if key == 'op' or key == 'field':
            continue
        problem_id, answer, pk, new_votes = request.POST.getlist(key)
        hinter_module = _location_to_module(problem_id, request, course_id)
        try:
            getattr(hinter_module, field)[answer][pk][1] = int(new_votes)
        except KeyError:
            return 'Invalid hint.'
        except ValueError:
            return '{inp} is not a valid vote count.  Please submit an integer.'.format(
                inp=str(new_votes)
            )
        hinter_module.save()


def add_hint(request, course_id, field):
    """
    Add a new hint.  `request.POST`:
    op
    field
    problem - The problem id
    answer - The answer to which a hint will be added
    hint - The text of the hint
    """

    problem_id = request.POST['problem']
    answer = request.POST['answer']
    hint_text = request.POST['hint']
    hinter_module = _location_to_module(problem_id, request, course_id)
    if not hinter_module.validate_answer(answer):
        return 'Invalid answer for this problem: {ans}'.format(ans=answer)
    hint_dict = getattr(hinter_module, field)
    if answer not in hint_dict:
        hint_dict[answer] = {}
    hint_dict[answer][hinter_module.hint_pk] = [hint_text, 1]
    hinter_module.save()


def approve(request, course_id, field):
    """
    Approve a list of hints, moving them from the mod_queue to the real
    hint list.  POST:
    op, field
    (some number) -> [problem, answer, pk]

    The numbered fields are analogous to those in `delete_hints` and `change_votes`.
    """

    for key in request.POST:
        if key == 'op' or key == 'field':
            continue
        problem_id, answer, pk = request.POST.getlist(key)
        hinter_module = _location_to_module(problem_id, request, course_id)
        try:
            transfer_hint = copy.copy(hinter_module.mod_queue[answer][pk])
        except KeyError:
            return 'Unable to find hint.'
        del hinter_module.mod_queue[answer][pk]
        if answer not in hinter_module.hints:
            hinter_module.hints[answer] = {}
        hinter_module.hints[answer][pk] = transfer_hint
        hinter_module.save()
