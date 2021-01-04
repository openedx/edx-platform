"""
Instructor API endpoint urls.
"""


from django.conf.urls import url

from lms.djangoapps.instructor.views import api, gradebook_api

urlpatterns = [
    url(r'^students_update_enrollment$', api.students_update_enrollment, name='students_update_enrollment'),
    url(r'^register_and_enroll_students$', api.register_and_enroll_students, name='register_and_enroll_students'),
    url(r'^list_course_role_members$', api.list_course_role_members, name='list_course_role_members'),
    url(r'^modify_access$', api.modify_access, name='modify_access'),
    url(r'^bulk_beta_modify_access$', api.bulk_beta_modify_access, name='bulk_beta_modify_access'),
    url(r'^get_problem_responses$', api.get_problem_responses, name='get_problem_responses'),
    url(r'^get_grading_config$', api.get_grading_config, name='get_grading_config'),
    url(r'^get_students_features(?P<csv>/csv)?$', api.get_students_features, name='get_students_features'),
    url(r'^get_issued_certificates/$', api.get_issued_certificates, name='get_issued_certificates'),
    url(r'^get_students_who_may_enroll$', api.get_students_who_may_enroll, name='get_students_who_may_enroll'),
    url(r'^get_anon_ids$', api.get_anon_ids, name='get_anon_ids'),
    url(r'^get_student_enrollment_status$', api.get_student_enrollment_status, name="get_student_enrollment_status"),
    url(r'^get_student_progress_url$', api.get_student_progress_url, name='get_student_progress_url'),
    url(r'^reset_student_attempts$', api.reset_student_attempts, name='reset_student_attempts'),
    url(r'^rescore_problem$', api.rescore_problem, name='rescore_problem'),
    url(r'^override_problem_score$', api.override_problem_score, name='override_problem_score'),
    url(r'^reset_student_attempts_for_entrance_exam$', api.reset_student_attempts_for_entrance_exam,
        name='reset_student_attempts_for_entrance_exam'),
    url(r'^rescore_entrance_exam$', api.rescore_entrance_exam, name='rescore_entrance_exam'),
    url(r'^list_entrance_exam_instructor_tasks', api.list_entrance_exam_instructor_tasks,
        name='list_entrance_exam_instructor_tasks'),
    url(r'^mark_student_can_skip_entrance_exam', api.mark_student_can_skip_entrance_exam,
        name='mark_student_can_skip_entrance_exam'),
    url(r'^list_instructor_tasks$', api.list_instructor_tasks, name='list_instructor_tasks'),
    url(r'^list_background_email_tasks$', api.list_background_email_tasks, name='list_background_email_tasks'),
    url(r'^list_email_content$', api.list_email_content, name='list_email_content'),
    url(r'^list_forum_members$', api.list_forum_members, name='list_forum_members'),
    url(r'^update_forum_role_membership$', api.update_forum_role_membership, name='update_forum_role_membership'),
    url(r'^send_email$', api.send_email, name='send_email'),
    url(r'^change_due_date$', api.change_due_date, name='change_due_date'),
    url(r'^reset_due_date$', api.reset_due_date, name='reset_due_date'),
    url(r'^show_unit_extensions$', api.show_unit_extensions, name='show_unit_extensions'),
    url(r'^show_student_extensions$', api.show_student_extensions, name='show_student_extensions'),

    # proctored exam downloads...
    url(r'^get_proctored_exam_results$', api.get_proctored_exam_results, name='get_proctored_exam_results'),

    # Grade downloads...
    url(r'^list_report_downloads$', api.list_report_downloads, name='list_report_downloads'),
    url(r'^calculate_grades_csv$', api.calculate_grades_csv, name='calculate_grades_csv'),
    url(r'^problem_grade_report$', api.problem_grade_report, name='problem_grade_report'),

    # Reports..
    url(r'^get_course_survey_results$', api.get_course_survey_results, name='get_course_survey_results'),
    url(r'^export_ora2_data', api.export_ora2_data, name='export_ora2_data'),

    url(r'^export_ora2_submission_files', api.export_ora2_submission_files,
        name='export_ora2_submission_files'),

    # spoc gradebook
    url(r'^gradebook$', gradebook_api.spoc_gradebook, name='spoc_gradebook'),

    url(r'^gradebook/(?P<offset>[0-9]+)$', gradebook_api.spoc_gradebook, name='spoc_gradebook'),

    # Cohort management
    url(r'^add_users_to_cohorts$', api.add_users_to_cohorts, name='add_users_to_cohorts'),

    # Certificates
    url(r'^generate_example_certificates$', api.generate_example_certificates, name='generate_example_certificates'),
    url(r'^enable_certificate_generation$', api.enable_certificate_generation, name='enable_certificate_generation'),
    url(r'^start_certificate_generation', api.start_certificate_generation, name='start_certificate_generation'),
    url(r'^start_certificate_regeneration', api.start_certificate_regeneration, name='start_certificate_regeneration'),
    url(r'^certificate_exception_view/$', api.certificate_exception_view, name='certificate_exception_view'),
    url(r'^generate_certificate_exceptions/(?P<generate_for>[^/]*)', api.generate_certificate_exceptions,
        name='generate_certificate_exceptions'),
    url(r'^generate_bulk_certificate_exceptions', api.generate_bulk_certificate_exceptions,
        name='generate_bulk_certificate_exceptions'),
    url(r'^certificate_invalidation_view/$', api.certificate_invalidation_view, name='certificate_invalidation_view'),
]
