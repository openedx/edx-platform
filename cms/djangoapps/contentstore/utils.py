from django.conf import settings
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError

DIRECT_ONLY_CATEGORIES = ['course', 'chapter', 'sequential', 'about', 'static_tab', 'course_info']

def get_modulestore(location):
    """
    Returns the correct modulestore to use for modifying the specified location
    """
    if not isinstance(location, Location):
        location = Location(location)
        
    if location.category in DIRECT_ONLY_CATEGORIES:
        return modulestore('direct')
    else:
        return modulestore()

def get_course_location_for_item(location):
    '''
    cdodge: for a given Xmodule, return the course that it belongs to
    NOTE: This makes a lot of assumptions about the format of the course location
    Also we have to assert that this module maps to only one course item - it'll throw an
    assert if not
    '''
    item_loc = Location(location)

    # check to see if item is already a course, if so we can skip this
    if item_loc.category != 'course':
        # @hack! We need to find the course location however, we don't
        # know the 'name' parameter in this context, so we have
        # to assume there's only one item in this query even though we are not specifying a name
        course_search_location = ['i4x', item_loc.org, item_loc.course, 'course', None]
        courses = modulestore().get_items(course_search_location)

        # make sure we found exactly one match on this above course search
        found_cnt = len(courses)
        if found_cnt == 0:
            raise Exception('Could not find course at {0}'.format(course_search_location))

        if found_cnt > 1:
            raise Exception('Found more than one course at {0}. There should only be one!!! Dump = {1}'.format(course_search_location, courses))

        location = courses[0].location

    return location

def get_course_for_item(location):
    '''
    cdodge: for a given Xmodule, return the course that it belongs to
    NOTE: This makes a lot of assumptions about the format of the course location
    Also we have to assert that this module maps to only one course item - it'll throw an
    assert if not
    '''
    item_loc = Location(location)

    # @hack! We need to find the course location however, we don't
    # know the 'name' parameter in this context, so we have
    # to assume there's only one item in this query even though we are not specifying a name
    course_search_location = ['i4x', item_loc.org, item_loc.course, 'course', None]
    courses = modulestore().get_items(course_search_location)

    # make sure we found exactly one match on this above course search
    found_cnt = len(courses)
    if found_cnt == 0:
        raise BaseException('Could not find course at {0}'.format(course_search_location))

    if found_cnt > 1:
        raise BaseException('Found more than one course at {0}. There should only be one!!! Dump = {1}'.format(course_search_location, courses))

    return courses[0]


def get_lms_link_for_item(location, preview=False):
    if settings.LMS_BASE is not None:
        lms_link = "//{preview}{lms_base}/courses/{course_id}/jump_to/{location}".format(
            preview='preview.' if preview else '',
            lms_base=settings.LMS_BASE,
            course_id=get_course_id(location),
            location=Location(location)
        )
    else:
        lms_link = None

    return lms_link

def get_lms_link_for_about_page(location):
    """
    Returns the url to the course about page from the location tuple.
    """
    if settings.LMS_BASE is not None:
        lms_link = "//{lms_base}/courses/{course_id}/about".format(
            lms_base=settings.LMS_BASE,
            course_id=get_course_id(location)
        )
    else:
        lms_link = None

    return lms_link

def get_course_id(location):
    """
    Returns the course_id from a given the location tuple.
    """
    # TODO: These will need to be changed to point to the particular instance of this problem in the particular course
    return modulestore().get_containing_courses(Location(location))[0].id

class UnitState(object):
    draft = 'draft'
    private = 'private'
    public = 'public'


def compute_unit_state(unit):
    """
    Returns whether this unit is 'draft', 'public', or 'private'.

    'draft' content is in the process of being edited, but still has a previous
        version visible in the LMS
    'public' content is locked and visible in the LMS
    'private' content is editabled and not visible in the LMS
    """

    if unit.cms.is_draft:
        try:
            modulestore('direct').get_item(unit.location)
            return UnitState.draft
        except ItemNotFoundError:
            return UnitState.private
    else:
        return UnitState.public


def get_date_display(date):
    return date.strftime("%d %B, %Y at %I:%M %p")

def update_item(location, value):
    """
    If value is None, delete the db entry. Otherwise, update it using the correct modulestore.
    """
    if value is None:
        get_modulestore(location).delete_item(location)
    else:
        get_modulestore(location).update_item(location, value)
