"""
Instructor API endpoint urls.
"""

from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',

    url(r'^students_update_enrollment$',
        'lms.djangoapps.instructor.views.api.students_update_enrollment', name="students_update_enrollment"),
    url(r'^register_and_enroll_students$',
        'lms.djangoapps.instructor.views.api.register_and_enroll_students', name="register_and_enroll_students"),
    url(r'^list_course_role_members$',
        'lms.djangoapps.instructor.views.api.list_course_role_members', name="list_course_role_members"),
    url(r'^modify_access$',
        'lms.djangoapps.instructor.views.api.modify_access', name="modify_access"),
    url(r'^bulk_beta_modify_access$',
        'lms.djangoapps.instructor.views.api.bulk_beta_modify_access', name="bulk_beta_modify_access"),
    url(r'^get_problem_responses$',
        'lms.djangoapps.instructor.views.api.get_problem_responses', name="get_problem_responses"),
    url(r'^get_grading_config$',
        'lms.djangoapps.instructor.views.api.get_grading_config', name="get_grading_config"),
    url(r'^get_students_features(?P<csv>/csv)?$',
        'lms.djangoapps.instructor.views.api.get_students_features', name="get_students_features"),
    url(r'^get_issued_certificates/$',
        'lms.djangoapps.instructor.views.api.get_issued_certificates', name="get_issued_certificates"),
    url(r'^get_students_who_may_enroll$',
        'lms.djangoapps.instructor.views.api.get_students_who_may_enroll', name="get_students_who_may_enroll"),
    url(r'^get_user_invoice_preference$',
        'lms.djangoapps.instructor.views.api.get_user_invoice_preference', name="get_user_invoice_preference"),
    url(r'^get_sale_records(?P<csv>/csv)?$',
        'lms.djangoapps.instructor.views.api.get_sale_records', name="get_sale_records"),
    url(r'^get_sale_order_records$',
        'lms.djangoapps.instructor.views.api.get_sale_order_records', name="get_sale_order_records"),
    url(r'^sale_validation_url$',
        'lms.djangoapps.instructor.views.api.sale_validation', name="sale_validation"),
    url(r'^get_anon_ids$',
        'lms.djangoapps.instructor.views.api.get_anon_ids', name="get_anon_ids"),
    url(r'^get_student_progress_url$',
        'lms.djangoapps.instructor.views.api.get_student_progress_url', name="get_student_progress_url"),
    url(r'^reset_student_attempts$',
        'lms.djangoapps.instructor.views.api.reset_student_attempts', name="reset_student_attempts"),
    url(
        r'^rescore_problem$',
        'lms.djangoapps.instructor.views.api.rescore_problem',
        name="rescore_problem"
    ), url(
        r'^reset_student_attempts_for_entrance_exam$',
        'lms.djangoapps.instructor.views.api.reset_student_attempts_for_entrance_exam',
        name="reset_student_attempts_for_entrance_exam"
    ), url(
        r'^rescore_entrance_exam$',
        'lms.djangoapps.instructor.views.api.rescore_entrance_exam',
        name="rescore_entrance_exam"
    ), url(
        r'^list_entrance_exam_instructor_tasks',
        'lms.djangoapps.instructor.views.api.list_entrance_exam_instructor_tasks',
        name="list_entrance_exam_instructor_tasks"
    ), url(
        r'^mark_student_can_skip_entrance_exam',
        'lms.djangoapps.instructor.views.api.mark_student_can_skip_entrance_exam',
        name="mark_student_can_skip_entrance_exam"
    ),

    url(r'^list_instructor_tasks$',
        'lms.djangoapps.instructor.views.api.list_instructor_tasks', name="list_instructor_tasks"),
    url(r'^list_background_email_tasks$',
        'lms.djangoapps.instructor.views.api.list_background_email_tasks', name="list_background_email_tasks"),
    url(r'^list_email_content$',
        'lms.djangoapps.instructor.views.api.list_email_content', name="list_email_content"),
    url(r'^list_forum_members$',
        'lms.djangoapps.instructor.views.api.list_forum_members', name="list_forum_members"),
    url(r'^update_forum_role_membership$',
        'lms.djangoapps.instructor.views.api.update_forum_role_membership', name="update_forum_role_membership"),
    url(r'^send_email$',
        'lms.djangoapps.instructor.views.api.send_email', name="send_email"),
    url(r'^change_due_date$', 'lms.djangoapps.instructor.views.api.change_due_date',
        name='change_due_date'),
    url(r'^reset_due_date$', 'lms.djangoapps.instructor.views.api.reset_due_date',
        name='reset_due_date'),
    url(r'^show_unit_extensions$', 'lms.djangoapps.instructor.views.api.show_unit_extensions',
        name='show_unit_extensions'),
    url(r'^show_student_extensions$', 'lms.djangoapps.instructor.views.api.show_student_extensions',
        name='show_student_extensions'),

    # proctored exam downloads...
    url(r'^get_proctored_exam_results$',
        'lms.djangoapps.instructor.views.api.get_proctored_exam_results', name="get_proctored_exam_results"),

    # Grade downloads...
    url(r'^list_report_downloads$',
        'lms.djangoapps.instructor.views.api.list_report_downloads', name="list_report_downloads"),
    url(r'calculate_grades_csv$',
        'lms.djangoapps.instructor.views.api.calculate_grades_csv', name="calculate_grades_csv"),
    url(r'problem_grade_report$',
        'lms.djangoapps.instructor.views.api.problem_grade_report', name="problem_grade_report"),

    # Financial Report downloads..
    url(r'^list_financial_report_downloads$',
        'lms.djangoapps.instructor.views.api.list_financial_report_downloads', name="list_financial_report_downloads"),

    # Registration Codes..
    url(r'get_registration_codes$',
        'lms.djangoapps.instructor.views.api.get_registration_codes', name="get_registration_codes"),
    url(r'generate_registration_codes$',
        'lms.djangoapps.instructor.views.api.generate_registration_codes', name="generate_registration_codes"),
    url(r'active_registration_codes$',
        'lms.djangoapps.instructor.views.api.active_registration_codes', name="active_registration_codes"),
    url(r'spent_registration_codes$',
        'lms.djangoapps.instructor.views.api.spent_registration_codes', name="spent_registration_codes"),

    # Reports..
    url(r'get_enrollment_report$',
        'lms.djangoapps.instructor.views.api.get_enrollment_report', name="get_enrollment_report"),
    url(r'get_exec_summary_report$',
        'lms.djangoapps.instructor.views.api.get_exec_summary_report', name="get_exec_summary_report"),
    url(r'get_course_survey_results$',
        'lms.djangoapps.instructor.views.api.get_course_survey_results', name="get_course_survey_results"),
    url(r'export_ora2_data',
        'lms.djangoapps.instructor.views.api.export_ora2_data', name="export_ora2_data"),

    # Coupon Codes..
    url(r'get_coupon_codes',
        'lms.djangoapps.instructor.views.api.get_coupon_codes', name="get_coupon_codes"),

    # spoc gradebook
    url(r'^gradebook$',
        'lms.djangoapps.instructor.views.gradebook_api.spoc_gradebook', name='spoc_gradebook'),

    url(r'^gradebook/(?P<offset>[0-9]+)$',
        'lms.djangoapps.instructor.views.gradebook_api.spoc_gradebook', name='spoc_gradebook'),

    # Cohort management
    url(r'add_users_to_cohorts$',
        'lms.djangoapps.instructor.views.api.add_users_to_cohorts', name="add_users_to_cohorts"),

    # Certificates
    url(r'^generate_example_certificates$',
        'lms.djangoapps.instructor.views.api.generate_example_certificates',
        name='generate_example_certificates'),

    url(r'^enable_certificate_generation$',
        'lms.djangoapps.instructor.views.api.enable_certificate_generation',
        name='enable_certificate_generation'),

    url(r'^start_certificate_generation',
        'lms.djangoapps.instructor.views.api.start_certificate_generation',
        name='start_certificate_generation'),

    url(r'^start_certificate_regeneration',
        'lms.djangoapps.instructor.views.api.start_certificate_regeneration',
        name='start_certificate_regeneration'),

    url(r'^certificate_exception_view/$',
        'lms.djangoapps.instructor.views.api.certificate_exception_view',
        name='certificate_exception_view'),

    url(r'^generate_certificate_exceptions/(?P<generate_for>[^/]*)',
        'lms.djangoapps.instructor.views.api.generate_certificate_exceptions',
        name='generate_certificate_exceptions'),

    url(r'^generate_bulk_certificate_exceptions',
        'lms.djangoapps.instructor.views.api.generate_bulk_certificate_exceptions',
        name='generate_bulk_certificate_exceptions'),

    url(r'^certificate_invalidation_view/$',
        'lms.djangoapps.instructor.views.api.certificate_invalidation_view',
        name='certificate_invalidation_view'),
)
