"""
LMS part of instructor grading:

- views + ajax handling
- calls the instructor grading service
"""

import logging

log = logging.getLogger(__name__)


class StaffGrading(object):
    """
    Wrap up functionality for staff grading of submissions--interface exposes get_html, ajax views.
    """

    def __init__(self, course):
        self.course = course

    def get_html(self):
        return "<b>Instructor grading!</b>"
        # context = {}
        # return render_to_string('courseware/instructor_grading_view.html', context)
