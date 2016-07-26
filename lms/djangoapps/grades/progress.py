"""
Progress Summary of a learner's course grades.
"""
from .new.course_grade import CourseGradeFactory


def summary(student, course):
    """
    Returns the CourseGrade for the given course and student.
    """
    return CourseGradeFactory(student).create(course)
