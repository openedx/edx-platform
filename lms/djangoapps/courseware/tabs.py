"""
Tabs configuration.  By the time the tab is being rendered, it's just a name,
link, and css class (CourseTab tuple).  Tabs are specified in course policy.
Each tab has a type, and possibly some type-specific parameters.

To add a new tab type, add a TabImpl to the VALID_TAB_TYPES dict below--it will
contain a validation function that checks whether config for the tab type is
valid, and a generator function that takes the config, user, and course, and
actually generates the CourseTab.
"""

from collections import namedtuple
import logging

from django.conf import settings
from django.core.urlresolvers import reverse

from courseware.access import has_access

log = logging.getLogger(__name__)

class InvalidTabsException(Exception):
    """
    A complaint about invalid tabs.
    """
    pass

CourseTab = namedtuple('CourseTab', 'name link is_active')

# encapsulate implementation for a tab:
#  - a validation function: takes the config dict and raises
#    InvalidTabsException if required fields are missing or otherwise
#    wrong.  (e.g. "is there a 'name' field?).  Validators can assume
#    that the type field is valid.
#
#  - a function that takes a config, a user, and a course, and active_page and
#    return a list of CourseTabs.  (e.g. "return a CourseTab with specified
#    name, link to courseware, and is_active=True/False").  The function can
#    assume that it is only called with configs of the appropriate type that
#    have passed the corresponding validator.
TabImpl = namedtuple('TabImpl', 'validator generator')


#####  Generators for various tabs.

def _courseware(tab, user, course, active_page):
    link = reverse('courseware', args=[course.id])
    return [CourseTab('Courseware', link, active_page == "courseware")]

def _course_info(tab, user, course, active_page):
    link = reverse('info', args=[course.id])
    return [CourseTab(tab['name'], link, active_page == "info")]

def _progress(tab, user, course, active_page):
    if user.is_authenticated():
        link = reverse('progress', args=[course.id])
        return [CourseTab(tab['name'], link, active_page == "progress")]
    return []

def _wiki(tab, user, course, active_page):
    if settings.WIKI_ENABLED:
        link = reverse('course_wiki', args=[course.id])
        return [CourseTab(tab['name'], link, active_page == 'wiki')]
    return []

def _discussion(tab, user, course, active_page):
    """
    This tab format only supports the new Berkeley discussion forums.
    """
    if settings.MITX_FEATURES.get('ENABLE_DISCUSSION_SERVICE'):
        link = reverse('django_comment_client.forum.views.forum_form_discussion',
                              args=[course.id])
        return [CourseTab(tab['name'], link, active_page=='discussion')]
    return []

def _external_link(tab, user, course, active_page):
    # external links are never active
    return [CourseTab(tab['name'], tab['link'], False)]


def _textbooks(tab, user, course, active_page):
    """
    Generates one tab per textbook.  Only displays if user is authenticated.
    """
    if user.is_authenticated() and settings.MITX_FEATURES.get('ENABLE_TEXTBOOK'):
        # since there can be more than one textbook, active_page is e.g. "book/0".
        return [CourseTab(textbook.title, reverse('book', args=[course.id, index]),
                          active_page=="textbook/{0}".format(index))
                for index, textbook in enumerate(course.textbooks)]
    return []

#### Validators


def key_checker(expected_keys):
    """
    Returns a function that checks that specified keys are present in a dict
    """
    def check(d):
        for k in expected_keys:
            if k not in d:
                raise InvalidTabsException("Key {0} not present in {1}"
                                           .format(k, d))
    return check


need_name = key_checker(['name'])

def null_validator(d):
    """
    Don't check anything--use for tabs that don't need any params. (e.g. textbook)
    """
    pass

##### The main tab config dict.

# type -> TabImpl
VALID_TAB_TYPES = {
    'courseware': TabImpl(null_validator, _courseware),
    'course_info': TabImpl(need_name, _course_info),
    'wiki': TabImpl(need_name, _wiki),
    'discussion': TabImpl(need_name, _discussion),
    'external_link': TabImpl(key_checker(['name', 'link']), _external_link),
    'textbooks': TabImpl(null_validator, _textbooks),
    'progress': TabImpl(need_name, _progress),
    }


### External interface below this.

def validate_tabs(course):
    """
    Check that the tabs set for the specified course is valid.  If it
    isn't, raise InvalidTabsException with the complaint.

    Specific rules checked:
    - if no tabs specified, that's fine
    - if tabs specified, first two must have type 'courseware' and 'course_info', in that order.
    - All the tabs must have a type in VALID_TAB_TYPES.

    """
    tabs = course.tabs
    if tabs is None:
        return

    if len(tabs) < 2:
        raise InvalidTabsException("Expected at least two tabs.  tabs: '{0}'".format(tabs))
    if tabs[0]['type'] != 'courseware':
        raise InvalidTabsException(
            "Expected first tab to have type 'courseware'.  tabs: '{0}'".format(tabs))
    if tabs[1]['type'] != 'course_info':
        raise InvalidTabsException(
            "Expected second tab to have type 'course_info'.  tabs: '{0}'".format(tabs))
    for t in tabs:
        if t['type'] not in VALID_TAB_TYPES:
            raise InvalidTabsException("Unknown tab type {0}. Known types: {1}"
                                       .format(t['type'], VALID_TAB_TYPES))
        # the type-specific validator checks the rest of the tab config
        VALID_TAB_TYPES[t['type']].validator(t)

    # Possible other checks: make sure tabs that should only appear once (e.g. courseware)
    # are actually unique (otherwise, will break active tag code)


def get_course_tabs(user, course, active_page):
    """
    Return the tabs to show a particular user, as a list of CourseTab items.
    """
    if not hasattr(course,'tabs') or not course.tabs:
        return get_default_tabs(user, course, active_page)

    # TODO (vshnayder): There needs to be a place to call this right after course
    # load, but not from inside xmodule, since that doesn't (and probably
    # shouldn't) know about the details of what tabs are supported, etc.
    validate_tabs(course)

    tabs = []
    for tab in course.tabs:
        # expect handlers to return lists--handles things that are turned off
        # via feature flags, and things like 'textbook' which might generate
        # multiple tabs.
        gen = VALID_TAB_TYPES[tab['type']].generator
        tabs.extend(gen(tab, user, course, active_page))

    # Instructor tab is special--automatically added if user is staff for the course
    if has_access(user, course, 'staff'):
        tabs.append(CourseTab('Instructor',
                              reverse('instructor_dashboard', args=[course.id]),
                              active_page == 'instructor'))
    return tabs


def get_default_tabs(user, course, active_page):

    # When calling the various _tab methods, can omit the 'type':'blah' from the
    # first arg, since that's only used for dispatch
    tabs = []
    tabs.extend(_courseware({''}, user, course, active_page))
    tabs.extend(_course_info({'name': 'Course Info'}, user, course, active_page))

    if hasattr(course, 'syllabus_present') and course.syllabus_present:
        link = reverse('syllabus', args=[course.id])
        tabs.append(CourseTab('Syllabus', link, active_page=='syllabus'))

    tabs.extend(_textbooks({}, user, course, active_page))

    ## If they have a discussion link specified, use that even if we feature
    ## flag discussions off. Disabling that is mostly a server safety feature
    ## at this point, and we don't need to worry about external sites.
    if course.discussion_link:
        tabs.append(CourseTab('Discussion', course.discussion_link, active_page == 'discussion'))
    elif settings.MITX_FEATURES.get('ENABLE_DISCUSSION_SERVICE'):
        link = reverse('django_comment_client.forum.views.forum_form_discussion',
                              args=[course.id])
        tabs.append(CourseTab('Discussion', link, active_page == 'discussion'))
    elif settings.MITX_FEATURES.get('ENABLE_DISCUSSION'):
        ## This is Askbot, which we should be retiring soon...
        tabs.append(CourseTab('Discussion', reverse('questions'), active_page == 'discussion'))

    tabs.extend(_wiki({'name': 'Wiki', 'type': 'wiki'}, user, course, active_page))

    if user.is_authenticated() and not course.hide_progress_tab:
        tabs.extend(_progress({'name': 'Progress'}, user, course, active_page))

    if has_access(user, course, 'staff'):
        link = reverse('instructor_dashboard', args=[course.id])
        tabs.append(CourseTab('Instructor', link, active_page=='instructor'))

    return tabs
