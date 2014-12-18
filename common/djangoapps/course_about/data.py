"""
Data Aggregation Layer for the Course About API. All knowledge of edx-platform specific data structures should
be hidden behind this layer.  The Python API (api.py) will access all data directly through this module.

This is responsible for combining data from the following resources:
* CourseDescriptor
* CourseAboutDescriptor

Eventually, additional Marketing metadata will also be accessed through this layer.

"""


def get_course_info_details(course_id):  # pylint: disable=unused-argument
    """Return all relative course metadata

    """
    pass
