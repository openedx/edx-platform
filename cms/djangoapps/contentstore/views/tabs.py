from access import has_access
from util.json_request import expect_json

from django.http import HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django_future.csrf import ensure_csrf_cookie
from mitxmako.shortcuts import render_to_response

from xmodule.modulestore import Location
from xmodule.modulestore.inheritance import own_metadata
from xmodule.modulestore.django import modulestore
from ..utils import get_course_for_item
from .access import get_location_and_verify_access

__all__ = ['edit_tabs', 'reorder_static_tabs', 'static_pages', 'edit_static']


def initialize_course_tabs(course):
    # set up the default tabs
    # I've added this because when we add static tabs, the LMS either expects a None for the tabs list or
    # at least a list populated with the minimal times
    # @TODO: I don't like the fact that the presentation tier is away of these data related constraints, let's find a better
    # place for this. Also rather than using a simple list of dictionaries a nice class model would be helpful here

    # This logic is repeated in xmodule/modulestore/tests/factories.py
    # so if you change anything here, you need to also change it there.
    course.tabs = [{"type": "courseware"},
                   {"type": "course_info", "name": "Course Info"},
                   {"type": "discussion", "name": "Discussion"},
                   {"type": "wiki", "name": "Wiki"},
                   {"type": "progress", "name": "Progress"}]

    modulestore('direct').update_metadata(course.location.url(), own_metadata(course))


@login_required
@expect_json
def reorder_static_tabs(request):
    tabs = request.POST['tabs']
    course = get_course_for_item(tabs[0])

    if not has_access(request.user, course.location):
        raise PermissionDenied()

    # get list of existing static tabs in course
    # make sure they are the same lengths (i.e. the number of passed in tabs equals the number
    # that we know about) otherwise we can drop some!

    existing_static_tabs = [t for t in course.tabs if t['type'] == 'static_tab']
    if len(existing_static_tabs) != len(tabs):
        return HttpResponseBadRequest()

    # load all reference tabs, return BadRequest if we can't find any of them
    tab_items = []
    for tab in tabs:
        item = modulestore('direct').get_item(Location(tab))
        if item is None:
            return HttpResponseBadRequest()

        tab_items.append(item)

    # now just go through the existing course_tabs and re-order the static tabs
    reordered_tabs = []
    static_tab_idx = 0
    for tab in course.tabs:
        if tab['type'] == 'static_tab':
            reordered_tabs.append({'type': 'static_tab',
                                   'name': tab_items[static_tab_idx].display_name,
                                   'url_slug': tab_items[static_tab_idx].location.name})
            static_tab_idx += 1
        else:
            reordered_tabs.append(tab)

    # OK, re-assemble the static tabs in the new order
    course.tabs = reordered_tabs
    modulestore('direct').update_metadata(course.location, own_metadata(course))
    return HttpResponse()


@login_required
@ensure_csrf_cookie
def edit_tabs(request, org, course, coursename):
    location = ['i4x', org, course, 'course', coursename]
    course_item = modulestore().get_item(location)

    # check that logged in user has permissions to this item
    if not has_access(request.user, location):
        raise PermissionDenied()

    # see tabs have been uninitialized (e.g. supporing courses created before tab support in studio)
    if course_item.tabs is None or len(course_item.tabs) == 0:
        initialize_course_tabs(course_item)

    # first get all static tabs from the tabs list
    # we do this because this is also the order in which items are displayed in the LMS
    static_tabs_refs = [t for t in course_item.tabs if t['type'] == 'static_tab']

    static_tabs = []
    for static_tab_ref in static_tabs_refs:
        static_tab_loc = Location(location)._replace(category='static_tab', name=static_tab_ref['url_slug'])
        static_tabs.append(modulestore('direct').get_item(static_tab_loc))

    components = [
        static_tab.location.url()
        for static_tab
        in static_tabs
    ]

    return render_to_response('edit-tabs.html', {
        'context_course': course_item,
        'components': components
    })


@login_required
@ensure_csrf_cookie
def static_pages(request, org, course, coursename):

    location = get_location_and_verify_access(request, org, course, coursename)

    course = modulestore().get_item(location)

    return render_to_response('static-pages.html', {
        'context_course': course,
    })


def edit_static(request, org, course, coursename):
    return render_to_response('edit-static-page.html', {})
