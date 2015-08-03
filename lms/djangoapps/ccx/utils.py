"""
CCX Enrollment operations for use by Coach APIs.

Does not include any access control, be sure to check access before calling.
"""
import logging

from .models import CustomCourseForEdX


log = logging.getLogger("edx.ccx")


def get_ccx_from_ccx_locator(course_id):
    """ helper function to allow querying ccx fields from templates """
    ccx_id = getattr(course_id, 'ccx', None)
    ccx = None
    if ccx_id:
        ccx = CustomCourseForEdX.objects.filter(id=ccx_id)
    if not ccx:
        log.warning(
            "CCX does not exist for course with id %s",
            course_id
        )
        return None
    return ccx[0]
