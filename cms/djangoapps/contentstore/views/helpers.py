"""
Helper methods for Studio views.
"""

from __future__ import absolute_import

import urllib

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from edxmako.shortcuts import render_to_string, render_to_response
from xblock.core import XBlock
from xmodule.modulestore.django import modulestore
from contentstore.utils import reverse_course_url, reverse_usage_url

__all__ = ['edge', 'event', 'landing']


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


def get_parent_xblock(xblock):
    """
    Returns the xblock that is the parent of the specified xblock, or None if it has no parent.
    """
    locator = xblock.location
    parent_location = modulestore().get_parent_location(locator)

    if parent_location is None:
        return None
    return modulestore().get_item(parent_location)


def is_unit(xblock, parent_xblock=None):
    """
    Returns true if the specified xblock is a vertical that is treated as a unit.
    A unit is a vertical that is a direct child of a sequential (aka a subsection).
    """
    if xblock.category == 'vertical':
        if parent_xblock is None:
            parent_xblock = get_parent_xblock(xblock)
        parent_category = parent_xblock.category if parent_xblock else None
        return parent_category == 'sequential'
    return False


def xblock_has_own_studio_page(xblock, parent_xblock=None):
    """
    Returns true if the specified xblock has an associated Studio page. Most xblocks do
    not have their own page but are instead shown on the page of their parent. There
    are a few exceptions:
      1. Courses
      2. Verticals that are either:
        - themselves treated as units
        - a direct child of a unit
      3. XBlocks that support children
    """
    category = xblock.category

    if is_unit(xblock, parent_xblock):
        return True
    elif category == 'vertical':
        if parent_xblock is None:
            parent_xblock = get_parent_xblock(xblock)
        return is_unit(parent_xblock) if parent_xblock else False

    # All other xblocks with children have their own page
    return xblock.has_children


def xblock_studio_url(xblock, parent_xblock=None):
    """
    Returns the Studio editing URL for the specified xblock.
    """
    if not xblock_has_own_studio_page(xblock, parent_xblock):
        return None
    category = xblock.category
    if category == 'course':
        return reverse_course_url('course_handler', xblock.location.course_key)
    elif category in ('chapter', 'sequential'):
        return u'{url}?show={usage_key}'.format(
            url=reverse_course_url('course_handler', xblock.location.course_key),
            usage_key=urllib.quote(unicode(xblock.location))
        )
    else:
        return reverse_usage_url('container_handler', xblock.location)


def xblock_type_display_name(xblock, default_display_name=None):
    """
    Returns the display name for the specified type of xblock. Note that an instance can be passed in
    for context dependent names, e.g. a vertical beneath a sequential is a Unit.

    :param xblock: An xblock instance or the type of xblock.
    :param default_display_name: The default value to return if no display name can be found.
    :return:
    """

    if hasattr(xblock, 'category'):
        category = xblock.category
        if category == 'vertical' and not is_unit(xblock):
            return _('Vertical')
    else:
        category = xblock
    if category == 'chapter':
        return _('Section')
    elif category == 'sequential':
        return _('Subsection')
    elif category == 'vertical':
        return _('Unit')
    component_class = XBlock.load_class(category, select=settings.XBLOCK_SELECT_FUNCTION)
    if hasattr(component_class, 'display_name') and component_class.display_name.default:
        return _(component_class.display_name.default)
    else:
        return default_display_name


def xblock_primary_child_category(xblock):
    """
    Returns the primary child category for the specified xblock, or None if there is not a primary category.
    """
    category = xblock.category
    if category == 'course':
        return 'chapter'
    elif category == 'chapter':
        return 'sequential'
    elif category == 'sequential':
        return 'vertical'
    return None
