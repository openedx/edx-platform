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

from .module_render import get_module
from courseware.access import has_access
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from courseware.model_data import ModelDataCache

from open_ended_grading import open_ended_notifications

log = logging.getLogger(__name__)


class InvalidTabsException(Exception):
    """
    A complaint about invalid tabs.
    """
    pass

CourseTabBase = namedtuple('CourseTab', 'name link is_active has_img img')


def CourseTab(name, link, is_active, has_img=False, img=""):
    return CourseTabBase(name, link, is_active, has_img, img)

# encapsulate implementation for a tab:
#  - a validation function: takes the config dict and raises
#    InvalidTabsException if required fields are missing or otherwise
#    wrong.  (e.g. "is there a 'name' field?).  Validators can assume
#    that the type field is valid.
#
#  - a function that takes a config, a user, and a course, an active_page and
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
        return [CourseTab(tab['name'], link, active_page == 'discussion')]
    return []


def _external_link(tab, user, course, active_page):
    # external links are never active
    return [CourseTab(tab['name'], tab['link'], False)]


def _static_tab(tab, user, course, active_page):
    link = reverse('static_tab', args=[course.id, tab['url_slug']])
    active_str = 'static_tab_{0}'.format(tab['url_slug'])
    return [CourseTab(tab['name'], link, active_page == active_str)]


def _textbooks(tab, user, course, active_page):
    """
    Generates one tab per textbook.  Only displays if user is authenticated.
    """
    if user.is_authenticated() and settings.MITX_FEATURES.get('ENABLE_TEXTBOOK'):
        # since there can be more than one textbook, active_page is e.g. "book/0".
        return [CourseTab(textbook.title, reverse('book', args=[course.id, index]),
                          active_page == "textbook/{0}".format(index))
                for index, textbook in enumerate(course.textbooks)]
    return []

def _pdf_textbooks(tab, user, course, active_page):
    """
    Generates one tab per textbook.  Only displays if user is authenticated.
    """
    if user.is_authenticated():
        # since there can be more than one textbook, active_page is e.g. "book/0".
        return [CourseTab(textbook['tab_title'], reverse('pdf_book', args=[course.id, index]),
                          active_page == "pdftextbook/{0}".format(index))
                for index, textbook in enumerate(course.pdf_textbooks)]
    return []

def _html_textbooks(tab, user, course, active_page):
    """
    Generates one tab per textbook.  Only displays if user is authenticated.
    """
    if user.is_authenticated():
        # since there can be more than one textbook, active_page is e.g. "book/0".
        return [CourseTab(textbook['tab_title'], reverse('html_book', args=[course.id, index]),
                          active_page == "htmltextbook/{0}".format(index))
                for index, textbook in enumerate(course.html_textbooks)]
    return []

def _staff_grading(tab, user, course, active_page):
    if has_access(user, course, 'staff'):
        link = reverse('staff_grading', args=[course.id])

        tab_name = "Staff grading"

        notifications  = open_ended_notifications.staff_grading_notifications(course, user)
        pending_grading = notifications['pending_grading']
        img_path = notifications['img_path']

        tab = [CourseTab(tab_name, link, active_page == "staff_grading", pending_grading, img_path)]
        return tab
    return []


def _peer_grading(tab, user, course, active_page):

    if user.is_authenticated():
        link = reverse('peer_grading', args=[course.id])
        tab_name = "Peer grading"

        notifications = open_ended_notifications.peer_grading_notifications(course, user)
        pending_grading = notifications['pending_grading']
        img_path = notifications['img_path']

        tab = [CourseTab(tab_name, link, active_page == "peer_grading", pending_grading, img_path)]
        return tab
    return []


def _combined_open_ended_grading(tab, user, course, active_page):
    if user.is_authenticated():
        link = reverse('open_ended_notifications', args=[course.id])
        tab_name = "Open Ended Panel"

        notifications  = open_ended_notifications.combined_notifications(course, user)
        pending_grading = notifications['pending_grading']
        img_path = notifications['img_path']

        tab = [CourseTab(tab_name, link, active_page == "open_ended", pending_grading, img_path)]
        return tab
    return []

def _notes_tab(tab, user, course, active_page):
    if user.is_authenticated() and settings.MITX_FEATURES.get('ENABLE_STUDENT_NOTES'):
        link = reverse('notes', args=[course.id])
        return [CourseTab(tab['name'], link, active_page == 'notes')]
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
    'pdf_textbooks': TabImpl(null_validator, _pdf_textbooks),
    'html_textbooks': TabImpl(null_validator, _html_textbooks),
    'progress': TabImpl(need_name, _progress),
    'static_tab': TabImpl(key_checker(['name', 'url_slug']), _static_tab),
    'peer_grading': TabImpl(null_validator, _peer_grading),
    'staff_grading': TabImpl(null_validator, _staff_grading),
    'open_ended': TabImpl(null_validator, _combined_open_ended_grading),
    'notes': TabImpl(null_validator, _notes_tab)
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
    if not hasattr(course, 'tabs') or not course.tabs:
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

    if has_access(user, course, 'staff'):
        tabs.append(CourseTab('Instructor 2',
                              reverse('instructor_dashboard_2', args=[course.id]),
                              active_page == 'instructor_2'))
    return tabs


def get_discussion_link(course):
    """
    Return the URL for the discussion tab for the given `course`.

    If they have a discussion link specified, use that even if we disable
    discussions. Disabling discsussions is mostly a server safety feature at
    this point, and we don't need to worry about external sites. Otherwise,
    if the course has a discussion tab or uses the default tabs, return the
    discussion view URL. Otherwise, return None to indicate the lack of a
    discussion tab.
    """
    if course.discussion_link:
        return course.discussion_link
    elif not settings.MITX_FEATURES.get('ENABLE_DISCUSSION_SERVICE'):
        return None
    elif hasattr(course, 'tabs') and course.tabs and not any([tab['type'] == 'discussion' for tab in course.tabs]):
        return None
    else:
        return reverse('django_comment_client.forum.views.forum_form_discussion', args=[course.id])


def get_default_tabs(user, course, active_page):

    # When calling the various _tab methods, can omit the 'type':'blah' from the
    # first arg, since that's only used for dispatch
    tabs = []
    tabs.extend(_courseware({''}, user, course, active_page))
    tabs.extend(_course_info({'name': 'Course Info'}, user, course, active_page))

    if hasattr(course, 'syllabus_present') and course.syllabus_present:
        link = reverse('syllabus', args=[course.id])
        tabs.append(CourseTab('Syllabus', link, active_page == 'syllabus'))

    tabs.extend(_textbooks({}, user, course, active_page))

    discussion_link = get_discussion_link(course)
    if discussion_link:
        tabs.append(CourseTab('Discussion', discussion_link, active_page == 'discussion'))

    tabs.extend(_wiki({'name': 'Wiki', 'type': 'wiki'}, user, course, active_page))

    if user.is_authenticated() and not course.hide_progress_tab:
        tabs.extend(_progress({'name': 'Progress'}, user, course, active_page))

    if has_access(user, course, 'staff'):
        link = reverse('instructor_dashboard', args=[course.id])
        tabs.append(CourseTab('Instructor', link, active_page == 'instructor'))

    if has_access(user, course, 'staff'):
        tabs.append(CourseTab('Instructor 2',
                              reverse('instructor_dashboard_2', args=[course.id]),
                              active_page == 'instructor_2'))

    return tabs


def get_static_tab_by_slug(course, tab_slug):
    """
    Look for a tab with type 'static_tab' and the specified 'tab_slug'.  Returns
    the tab (a config dict), or None if not found.
    """
    if course.tabs is None:
        return None
    for tab in course.tabs:
        # The validation code checks that these exist.
        if tab['type'] == 'static_tab' and tab['url_slug'] == tab_slug:
            return tab

    return None


def get_static_tab_contents(request, course, tab):

    loc = Location(course.location.tag, course.location.org, course.location.course, 'static_tab', tab['url_slug'])
    model_data_cache = ModelDataCache.cache_for_descriptor_descendents(course.id,
        request.user, modulestore().get_instance(course.id, loc), depth=0)
    tab_module = get_module(request.user, request, loc, model_data_cache, course.id)

    logging.debug('course_module = {0}'.format(tab_module))

    html = ''

    if tab_module is not None:
        html = tab_module.get_html()

    return html
