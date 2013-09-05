from xmodule.modulestore import search
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError, NoPathToItem

def does_location_exist(course_id, location):
    """
    Checks to see if a valid module exists at a given location (ie has not been deleted)
    course_id - string course id
    location - string location
    """
    try:
        search.path_to_location(modulestore(), course_id, location)
        return True
    except ItemNotFoundError:
        # If the problem cannot be found at the location received from the grading controller server, it has been deleted by the course author.
        return False
    except NoPathToItem:
        # If the problem can be found, but there is no path to it, then it is a draft.
        return False
