"""
Module to define url helpers functions
"""
from urllib import urlencode
from xmodule.modulestore.search import path_to_location, navigation_index
from xmodule.modulestore.django import modulestore
from django.core.urlresolvers import reverse


def get_redirect_url(course_key, usage_key):
    """ Returns the redirect url back to courseware

    Args:
        course_id(str): Course Id string
        location(str): The location id of course component

    Raises:
        ItemNotFoundError if no data at the location or NoPathToItem if location not in any class

    Returns:
        Redirect url string
    """

    (
        course_key, chapter, section, vertical_unused,
        position, final_target_id
    ) = path_to_location(modulestore(), usage_key)

    # choose the appropriate view (and provide the necessary args) based on the
    # args provided by the redirect.
    # Rely on index to do all error handling and access control.
    if chapter is None:
        redirect_url = reverse('courseware', args=(unicode(course_key), ))
    elif section is None:
        redirect_url = reverse('courseware_chapter', args=(unicode(course_key), chapter))
    elif position is None:
        redirect_url = reverse(
            'courseware_section',
            args=(unicode(course_key), chapter, section)
        )
    else:
        # Here we use the navigation_index from the position returned from
        # path_to_location - we can only navigate to the topmost vertical at the
        # moment
        redirect_url = reverse(
            'courseware_position',
            args=(unicode(course_key), chapter, section, navigation_index(position))
        )
    redirect_url += "?{}".format(urlencode({'activate_block_id': unicode(final_target_id)}))
    return redirect_url


def get_redirect_url_for_global_staff(course_key, _next):
    """
    Returns the redirect url for staff enrollment

    Args:
        course_key(str): Course key string
        _next(str): Redirect url of course component
    """
    redirect_url = ("{url}?next={redirect}".format(
        url=reverse('enroll_staff', args=[unicode(course_key)]),
        redirect=_next))
    return redirect_url
