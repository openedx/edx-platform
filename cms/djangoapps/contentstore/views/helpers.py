import logging

from django.http import HttpResponse
from django.shortcuts import redirect
from edxmako.shortcuts import render_to_string, render_to_response
from xmodule.modulestore.django import loc_mapper, modulestore

__all__ = ['edge', 'event', 'landing']

EDITING_TEMPLATES = [
    "basic-modal", "modal-button", "edit-xblock-modal", "editor-mode-button", "upload-dialog", "image-modal",
    "add-xblock-component", "add-xblock-component-button", "add-xblock-component-menu",
    "add-xblock-component-menu-problem"
]

# points to the temporary course landing page with log in and sign up
def landing(request, org, course, coursename):
    return render_to_response('temp-course-landing.html', {})


# points to the temporary edge page
def edge(request):
    return redirect('/')


def event(request):
    '''
    A noop to swallow the analytics call so that cms methods don't spook and poor developers looking at
    console logs don't get distracted :-)
    '''
    return HttpResponse(status=204)


def render_from_lms(template_name, dictionary, context=None, namespace='main'):
    """
    Render a template using the LMS MAKO_TEMPLATES
    """
    return render_to_string(template_name, dictionary, context, namespace="lms." + namespace)


def _xmodule_recurse(item, action):
    for child in item.get_children():
        _xmodule_recurse(child, action)

    action(item)


def get_parent_xblock(xblock):
    """
    Returns the xblock that is the parent of the specified xblock, or None if it has no parent.
    """
    locator = xblock.location
    parent_locations = modulestore().get_parent_locations(locator, None)

    if len(parent_locations) == 0:
        return None
    elif len(parent_locations) > 1:
        logging.error('Multiple parents have been found for %s', unicode(locator))
    return modulestore().get_item(parent_locations[0])


def is_unit(xblock):
    """
    Returns true if the specified xblock is a vertical that is treated as a unit.
    A unit is a vertical that is a direct child of a sequential (aka a subsection).
    """
    if xblock.category == 'vertical':
        parent_xblock = get_parent_xblock(xblock)
        parent_category = parent_xblock.category if parent_xblock else None
        return parent_category == 'sequential'
    return False


def xblock_has_own_studio_page(xblock):
    """
    Returns true if the specified xblock has an associated Studio page. Most xblocks do
    not have their own page but are instead shown on the page of their parent. There
    are a few exceptions:
      1. Courses
      2. Verticals that are either:
        - themselves treated as units (in which case they are shown on a unit page)
        - a direct child of a unit (in which case they are shown on a container page)
      3. XBlocks with children, except for:
        - sequentials (aka subsections)
        - chapters (aka sections)
    """
    category = xblock.category

    if is_unit(xblock):
        return True
    elif category == 'vertical':
        parent_xblock = get_parent_xblock(xblock)
        return is_unit(parent_xblock) if parent_xblock else False
    elif category in ('sequential', 'chapter'):
        return False

    # All other xblocks with children have their own page
    return xblock.has_children


def xblock_studio_url(xblock, course=None):
    """
    Returns the Studio editing URL for the specified xblock.
    """
    if not xblock_has_own_studio_page(xblock):
        return None
    category = xblock.category
    parent_xblock = get_parent_xblock(xblock)
    parent_category = parent_xblock.category if parent_xblock else None
    if category == 'course':
        prefix = 'course'
    elif category == 'vertical' and parent_category == 'sequential':
        prefix = 'unit'     # only show the unit page for verticals directly beneath a subsection
    else:
        prefix = 'container'
    course_id = None
    if course:
        course_id = course.location.course_id
    locator = loc_mapper().translate_location(course_id, xblock.location, published=False)
    return locator.url_reverse(prefix)
