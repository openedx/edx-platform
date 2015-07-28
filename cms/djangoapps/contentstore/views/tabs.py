"""
Views related to course tabs
"""
from student.auth import has_course_author_access
from util.json_request import expect_json, JsonResponse

from django.http import HttpResponseNotFound
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from edxmako.shortcuts import render_to_response
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.tabs import CourseTabList, CourseTab, InvalidTabsException, StaticTab
from opaque_keys.edx.keys import CourseKey, UsageKey

from ..utils import get_lms_link_for_item

__all__ = ['tabs_handler']


@expect_json
@login_required
@ensure_csrf_cookie
@require_http_methods(("GET", "POST", "PUT"))
def tabs_handler(request, course_key_string):
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
    course_key = CourseKey.from_string(course_key_string)
    if not has_course_author_access(request.user, course_key):
        raise PermissionDenied()

    course_item = modulestore().get_course(course_key)

    if 'application/json' in request.META.get('HTTP_ACCEPT', 'application/json'):
        if request.method == 'GET':
            raise NotImplementedError('coming soon')
        else:
            if 'tabs' in request.json:
                return reorder_tabs_handler(course_item, request)
            elif 'tab_id_locator' in request.json:
                return edit_tab_handler(course_item, request)
            else:
                raise NotImplementedError('Creating or changing tab content is not supported.')

    elif request.method == 'GET':  # assume html
        # get all tabs from the tabs list: static tabs (a.k.a. user-created tabs) and built-in tabs
        # present in the same order they are displayed in LMS

        tabs_to_render = []
        for tab in CourseTabList.iterate_displayable(course_item, inline_collections=False):
            if isinstance(tab, StaticTab):
                # static tab needs its locator information to render itself as an xmodule
                static_tab_loc = course_key.make_usage_key('static_tab', tab.url_slug)
                tab.locator = static_tab_loc
            tabs_to_render.append(tab)

        return render_to_response('edit-tabs.html', {
            'context_course': course_item,
            'tabs_to_render': tabs_to_render,
            'lms_link': get_lms_link_for_item(course_item.location),
        })
    else:
        return HttpResponseNotFound()


def reorder_tabs_handler(course_item, request):
    """
    Helper function for handling reorder of tabs request
    """

    # Tabs are identified by tab_id or locators.
    # The locators are used to identify static tabs since they are xmodules.
    # Although all tabs have tab_ids, newly created static tabs do not know
    # their tab_ids since the xmodule editor uses only locators to identify new objects.
    requested_tab_id_locators = request.json['tabs']

    # original tab list in original order
    old_tab_list = course_item.tabs

    # create a new list in the new order
    new_tab_list = []
    for tab_id_locator in requested_tab_id_locators:
        tab = get_tab_by_tab_id_locator(old_tab_list, tab_id_locator)
        if tab is None:
            return JsonResponse(
                {"error": "Tab with id_locator '{0}' does not exist.".format(tab_id_locator)}, status=400
            )
        new_tab_list.append(tab)

    # the old_tab_list may contain additional tabs that were not rendered in the UI because of
    # global or course settings.  so add those to the end of the list.
    non_displayed_tabs = set(old_tab_list) - set(new_tab_list)
    new_tab_list.extend(non_displayed_tabs)

    # validate the tabs to make sure everything is Ok (e.g., did the client try to reorder unmovable tabs?)
    try:
        CourseTabList.validate_tabs(new_tab_list)
    except InvalidTabsException, exception:
        return JsonResponse(
            {"error": "New list of tabs is not valid: {0}.".format(str(exception))}, status=400
        )

    # persist the new order of the tabs
    course_item.tabs = new_tab_list
    modulestore().update_item(course_item, request.user.id)

    return JsonResponse()


def edit_tab_handler(course_item, request):
    """
    Helper function for handling requests to edit settings of a single tab
    """

    # Tabs are identified by tab_id or locator
    tab_id_locator = request.json['tab_id_locator']

    # Find the given tab in the course
    tab = get_tab_by_tab_id_locator(course_item.tabs, tab_id_locator)
    if tab is None:
        return JsonResponse(
            {"error": "Tab with id_locator '{0}' does not exist.".format(tab_id_locator)}, status=400
        )

    if 'is_hidden' in request.json:
        # set the is_hidden attribute on the requested tab
        tab.is_hidden = request.json['is_hidden']
        modulestore().update_item(course_item, request.user.id)
    else:
        raise NotImplementedError('Unsupported request to edit tab: {0}'.format(request.json))

    return JsonResponse()


def get_tab_by_tab_id_locator(tab_list, tab_id_locator):
    """
    Look for a tab with the specified tab_id or locator.  Returns the first matching tab.
    """
    if 'tab_id' in tab_id_locator:
        tab = CourseTabList.get_tab_by_id(tab_list, tab_id_locator['tab_id'])
    elif 'tab_locator' in tab_id_locator:
        tab = get_tab_by_locator(tab_list, tab_id_locator['tab_locator'])
    return tab


def get_tab_by_locator(tab_list, usage_key_string):
    """
    Look for a tab with the specified locator.  Returns the first matching tab.
    """
    tab_location = UsageKey.from_string(usage_key_string)
    item = modulestore().get_item(tab_location)
    static_tab = StaticTab(
        name=item.display_name,
        url_slug=item.location.name,
    )
    return CourseTabList.get_tab_by_id(tab_list, static_tab.tab_id)


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
    modulestore().update_item(course, ModuleStoreEnum.UserID.primitive_command)


def primitive_insert(course, num, tab_type, name):
    "Inserts a new tab at the given number (0 based)."
    validate_args(num, tab_type)
    new_tab = CourseTab.from_json({u'type': unicode(tab_type), u'name': unicode(name)})
    tabs = course.tabs
    tabs.insert(num, new_tab)
    modulestore().update_item(course, ModuleStoreEnum.UserID.primitive_command)
