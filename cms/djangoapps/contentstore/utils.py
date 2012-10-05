from django.conf import settings
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.draft import DRAFT
from xmodule.modulestore.exceptions import ItemNotFoundError


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
            raise BaseException('Could not find course at {0}'.format(course_search_location))

        if found_cnt > 1:
            raise BaseException('Found more than one course at {0}. There should only be one!!!'.format(course_search_location))

        location = courses[0].location

    return location


def get_lms_link_for_item(location):
    if settings.LMS_BASE is not None:
        lms_link = "{lms_base}/courses/{course_id}/jump_to/{location}".format(
            lms_base=settings.LMS_BASE,
            # TODO: These will need to be changed to point to the particular instance of this problem in the particular course
            course_id = modulestore().get_containing_courses(location)[0].id,
            location=location,
        )
    else:
        lms_link = None

    return lms_link


def compute_unit_state(unit):
    """
    Returns whether this unit is 'draft', 'public', or 'private'.

    'draft' content is in the process of being edited, but still has a previous
        version visible in the LMS
    'public' content is locked and visible in the LMS
    'private' content is editabled and not visible in the LMS
    """

    if unit.metadata.get('is_draft', False):
        try:
            modulestore('direct').get_item(unit.location)
            return 'draft'
        except ItemNotFoundError:
            return 'private'
    else:
        return 'public'
