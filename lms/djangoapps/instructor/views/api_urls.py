"""
Instructor API endpoint urls.
"""


from django.conf.urls import patterns, url

urlpatterns = patterns('',  # nopep8
    url(r'^students_update_enrollment$',
        'instructor.views.api.students_update_enrollment', name="students_update_enrollment"),
    url(r'^list_course_role_members$',
        'instructor.views.api.list_course_role_members', name="list_course_role_members"),
    url(r'^modify_access$',
        'instructor.views.api.modify_access', name="modify_access"),
    url(r'^get_grading_config$',
        'instructor.views.api.get_grading_config', name="get_grading_config"),
    url(r'^get_students_features(?P<csv>/csv)?$',
        'instructor.views.api.get_students_features', name="get_students_features"),
    url(r'^get_distribution$',
        'instructor.views.api.get_distribution', name="get_distribution"),
    url(r'^get_student_progress_url$',
        'instructor.views.api.get_student_progress_url', name="get_student_progress_url"),
    url(r'^reset_student_attempts$',
        'instructor.views.api.reset_student_attempts', name="reset_student_attempts"),
    url(r'^rescore_problem$',
        'instructor.views.api.rescore_problem', name="rescore_problem"),
    url(r'^list_instructor_tasks$',
        'instructor.views.api.list_instructor_tasks', name="list_instructor_tasks"),
    url(r'^list_forum_members$',
        'instructor.views.api.list_forum_members', name="list_forum_members"),
    url(r'^update_forum_role_membership$',
        'instructor.views.api.update_forum_role_membership', name="update_forum_role_membership"),
)
