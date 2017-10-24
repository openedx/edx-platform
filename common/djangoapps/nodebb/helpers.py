import collections
from courseware.tabs import get_course_tab_list
from lms.djangoapps.grades.new.course_grade import CourseGradeFactory
from django.core.urlresolvers import reverse


def get_course_related_tabs(request, course):
    """
        Return list of tabs data as dictionary
    """

    course_tabs = get_course_tab_list(request, course)

    tabs_dict = collections.OrderedDict()
    for idx, tab in enumerate(course_tabs):
        tab_name = tab.name.lower()
        tab_link = tab.link_func(course, reverse)

        if tab_name == "discussion":
            tab_link = tab_link.replace("forum", "nodebb")

        tabs_dict[tab.name] = {'link': tab_link, 'name': tab.name, 'type': tab.type}

    return tabs_dict


def get_all_course_progress(student, course):
    """
        Return course overall progress percentage for a student
    """

    course_grade = CourseGradeFactory().create(student, course)
    courseware_summary = course_grade.chapter_grades

    total_score = 0
    earned_score = 0

    for week in courseware_summary:
        sections = week.get('sections', [])

        for section in sections:
            total_score += section.all_total.possible
            earned_score += section.all_total.earned

    if total_score:
        average = earned_score / total_score
        percentage = average * 100
    else:
        percentage = 0

    return int(percentage)
