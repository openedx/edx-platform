"""
Views related to course tabs
"""
from access import has_course_access
from util.json_request import expect_json, JsonResponse

from django.http import HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django_future.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from edxmako.shortcuts import render_to_response
from xmodule.modulestore import Location
from xmodule.modulestore.inheritance import own_metadata
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.django import loc_mapper
from xmodule.modulestore.locator import BlockUsageLocator

from ..utils import get_modulestore

from django.utils.translation import ugettext as _

__all__ = ['tabs_handler']


def initialize_course_tabs(course):
    """
    set up the default tabs
    I've added this because when we add static tabs, the LMS either expects a None for the tabs list or
    at least a list populated with the minimal times
    @TODO: I don't like the fact that the presentation tier is away of these data related constraints, let's find a better
    place for this. Also rather than using a simple list of dictionaries a nice class model would be helpful here
    """

    # This logic is repeated in xmodule/modulestore/tests/factories.py
    # so if you change anything here, you need to also change it there.
    course.tabs = [
        {"type": "courseware", "name": _("Courseware")},
        {"type": "course_info", "name": _("Course Info")},
        {"type": "discussion", "name": _("Discussion")},
        {"type": "wiki", "name": _("Wiki")},
        {"type": "progress", "name": _("Progress")},
    ]

    modulestore('direct').update_metadata(course.location.url(), own_metadata(course))

@expect_json
@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT"))
def tabs_handler(request, tag=None, package_id=None, branch=None, version_guid=None, block=None):
    """
    The restful handler for static tabs.

    GET
        html: return page for editing static tabs
        json: not supported
    PUT or POST
        json: update the tab order. It is expected that the request body contains a JSON-encoded dict with entry "tabs".
        The value for "tabs" is an array of tab locators, indicating the desired order of the tabs.

    Creating a tab, deleting a tab, or changing its contents is not supported through this method.
    Instead use the general xblock URL (see item.xblock_handler).
    """
    locator = BlockUsageLocator(package_id=package_id, branch=branch, version_guid=version_guid, block_id=block)
    if not has_course_access(request.user, locator):
        raise PermissionDenied()

    old_location = loc_mapper().translate_locator_to_location(locator)
    store = get_modulestore(old_location)
    course_item = store.get_item(old_location)

    if 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'GET':
            raise NotImplementedError('coming soon')
        else:
            if 'tabs' in request.json:
                def get_location_for_tab(tab):
                    """  Returns the location (old-style) for a tab. """
                    return loc_mapper().translate_locator_to_location(BlockUsageLocator(tab))

                tabs = request.json['tabs']

                # get list of existing static tabs in course
                # make sure they are the same lengths (i.e. the number of passed in tabs equals the number
                # that we know about) otherwise we will inadvertently drop some!
                existing_static_tabs = [t for t in course_item.tabs if t['type'] == 'static_tab']
                if len(existing_static_tabs) != len(tabs):
                    return JsonResponse(
                        {"error": "number of tabs must be {}".format(len(existing_static_tabs))}, status=400
                    )

                # load all reference tabs, return BadRequest if we can't find any of them
                tab_items = []
                for tab in tabs:
                    item = modulestore('direct').get_item(get_location_for_tab(tab))
                    if item is None:
                        return JsonResponse(
                            {"error": "no tab for found location {}".format(tab)}, status=400
                        )

                    tab_items.append(item)

                # now just go through the existing course_tabs and re-order the static tabs
                reordered_tabs = []
                static_tab_idx = 0
                for tab in course_item.tabs:
                    if tab['type'] == 'static_tab':
                        reordered_tabs.append(
                            {'type': 'static_tab',
                             'name': tab_items[static_tab_idx].display_name,
                             'url_slug': tab_items[static_tab_idx].location.name,
                            }
                        )
                        static_tab_idx += 1
                    else:
                        reordered_tabs.append(tab)

                # OK, re-assemble the static tabs in the new order
                course_item.tabs = reordered_tabs
                modulestore('direct').update_metadata(course_item.location, own_metadata(course_item))
                return JsonResponse()
            else:
                raise NotImplementedError('Creating or changing tab content is not supported.')
    elif request.method == 'GET':  # assume html
        # see tabs have been uninitialized (e.g. supporting courses created before tab support in studio)
        if course_item.tabs is None or len(course_item.tabs) == 0:
            initialize_course_tabs(course_item)

        # first get all static tabs from the tabs list
        # we do this because this is also the order in which items are displayed in the LMS
        static_tabs_refs = [t for t in course_item.tabs if t['type'] == 'static_tab']

        static_tabs = []
        for static_tab_ref in static_tabs_refs:
            static_tab_loc = old_location.replace(category='static_tab', name=static_tab_ref['url_slug'])
            static_tabs.append(modulestore('direct').get_item(static_tab_loc))

        components = [
            loc_mapper().translate_location(
                course_item.location.course_id, static_tab.location, False, True
            )
            for static_tab
            in static_tabs
        ]

        return render_to_response('edit-tabs.html', {
            'context_course': course_item,
            'components': components,
            'course_locator': locator
        })
    else:
        return HttpResponseNotFound()


# "primitive" tab edit functions driven by the command line.
# These should be replaced/deleted by a more capable GUI someday.
# Note that the command line UI identifies the tabs with 1-based
# indexing, but this implementation code is standard 0-based.

def validate_args(num, tab_type):
    "Throws for the disallowed cases."
    if num <= 1:
        raise ValueError('Tabs 1 and 2 cannot be edited')
    if tab_type == 'static_tab':
        raise ValueError('Tabs of type static_tab cannot be edited here (use Studio)')


def primitive_delete(course, num):
    "Deletes the given tab number (0 based)."
    tabs = course.tabs
    validate_args(num, tabs[num].get('type', ''))
    del tabs[num]
    # Note for future implementations: if you delete a static_tab, then Chris Dodge
    # points out that there's other stuff to delete beyond this element.
    # This code happens to not delete static_tab so it doesn't come up.
    modulestore('direct').update_metadata(course.location, own_metadata(course))


def primitive_insert(course, num, tab_type, name):
    "Inserts a new tab at the given number (0 based)."
    validate_args(num, tab_type)
    new_tab = {u'type': unicode(tab_type), u'name': unicode(name)}
    tabs = course.tabs
    tabs.insert(num, new_tab)
    modulestore('direct').update_metadata(course.location, own_metadata(course))

