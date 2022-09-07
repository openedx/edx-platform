"""
Temporary helpers as workarounds until we upgrade the platform
"""
import re


def replace_jump_with_resume(jump_link):
    """
    Replace jump_to in the url with resume_to is the link is recognized as a valid jump_to link (structure wise). no
    checking or validation on the course/course-content is performed

    ex: replace_jump_with_resume('/courses/a-course-id:whatever/jump_to/some/link@whatever')
    will return: '/courses/a-course-id:whatever/resume_to/some/link@whatever'

    :param jump_link: the link to be processed
    :return: link with resume_to
    """
    return re.sub(r'(.*)/courses/(.+)/jump_to/(.+)', r'\1/courses/\2/resume_to/\3', jump_link)
