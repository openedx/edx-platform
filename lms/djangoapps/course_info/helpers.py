# -*- coding:utf-8 -*-
from models import MainClassification,FirstClassification,SecondClassification,ThirdClassification,CourseClassification

def get_course_class(courses):
    CourseClass = [[course.course_id,course.MainClass] for course in CourseClassification.objects.all()]
    ret_courses = {}
    cats = []
    for main in MainClassification.objects.all().order_by('sequence'):
        cats.append({'id':main.id,'name':main.name,'seq':main.sequence,'show_opt':main.show_opt})
        ret_courses[main.id] = {'id':main.id,'name':main.name,'seq':main.sequence,'courses':[]}
    for course in courses:
        try:
            course_class = CourseClassification.objects.get(course_id=course.pk)
            ret_courses[course_class.MainClass.id]['courses'].append(course)
        except CourseClassification.DoesNotExist:
            pass
    return cats,ret_courses
