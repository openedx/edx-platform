"""
Instructor API endpoint urls.
"""

from django.conf.urls import patterns, url

urlpatterns = patterns(
    '',

    url(r'^students_update_enrollment$',
        'instructor.views.api.students_update_enrollment', name="students_update_enrollment"),
    url(r'^register_and_enroll_students$',
        'instructor.views.api.register_and_enroll_students', name="register_and_enroll_students"),
    url(r'^list_course_role_members$',
        'instructor.views.api.list_course_role_members', name="list_course_role_members"),
    url(r'^list_course_sections$',
        'instructor.views.api.list_course_sections', name="list_course_sections"),
    url(r'^list_course_problems$',
        'instructor.views.api.list_course_problems', name="list_course_problems"),
    url(r'^list_course_tree$',
        'instructor.views.api.list_course_tree', name="list_course_tree"),
    url(r'^modify_access$',
        'instructor.views.api.modify_access', name="modify_access"),
    url(r'^bulk_beta_modify_access$',
        'instructor.views.api.bulk_beta_modify_access', name="bulk_beta_modify_access"),
    url(r'^get_problem_responses$',
        'instructor.views.api.get_problem_responses', name="get_problem_responses"),
    url(r'^get_grading_config$',
        'instructor.views.api.get_grading_config', name="get_grading_config"),
    url(r'^get_all_students(?P<make_csv>/csv)?$',
        'instructor.views.api.get_all_students', name="get_all_students"),
    url(r'^save_query$',
        'instructor.views.api.save_query', name="save_query"),
    url(r'^get_saved_queries$',
        'instructor.views.api.get_saved_queries', name="get_saved_queries"),
    url(r'^get_temp_queries$',
        'instructor.views.api.get_temp_queries', name="get_temp_queries"),
    url(r'^get_single_query/(?P<inclusion>\S{2,3})/(?P<query_type>(Section|Problem))/(?P<state_type>\S+)/(?P<state_id>\S+)$',
        'instructor.views.api.get_single_query', name="get_single_query"),
    # the parameter-less url is here as a convenience because we don't know the params at the time of calling 'reverse
    url(r'^get_single_query',
        'instructor.views.api.get_single_query', name="get_single_query"),
    url(r'^delete_saved_query',
        'instructor.views.api.delete_saved_query', name="delete_saved_query"),
    url(r'^delete_temp_query_batch',
        'instructor.views.api.delete_temp_query_batch', name="delete_temp_query_batch"),
    url(r'^delete_temp_query',
        'instructor.views.api.delete_temp_query', name="delete_temp_query"),
    url(r'^save_group_name',
        'instructor.views.api.save_group_name', name="save_group_name"),
    url(r'^get_students_features(?P<csv>/csv)?$',
        'instructor.views.api.get_students_features', name="get_students_features"),
    url(r'^get_issued_certificates/$',
        'instructor.views.api.get_issued_certificates', name="get_issued_certificates"),
    url(r'^get_students_who_may_enroll$',
        'instructor.views.api.get_students_who_may_enroll', name="get_students_who_may_enroll"),
    url(r'^get_user_invoice_preference$',
        'instructor.views.api.get_user_invoice_preference', name="get_user_invoice_preference"),
    url(r'^get_sale_records(?P<csv>/csv)?$',
        'instructor.views.api.get_sale_records', name="get_sale_records"),
    url(r'^get_sale_order_records$',
        'instructor.views.api.get_sale_order_records', name="get_sale_order_records"),
    url(r'^sale_validation_url$',
        'instructor.views.api.sale_validation', name="sale_validation"),
    url(r'^get_anon_ids$',
        'instructor.views.api.get_anon_ids', name="get_anon_ids"),
    url(r'^get_student_progress_url$',
        'instructor.views.api.get_student_progress_url', name="get_student_progress_url"),
    url(r'^reset_student_attempts$',
        'instructor.views.api.reset_student_attempts', name="reset_student_attempts"),
    url(
        r'^rescore_problem$',
        'instructor.views.api.rescore_problem',
        name="rescore_problem"
    ), url(
        r'^reset_student_attempts_for_entrance_exam$',
        'instructor.views.api.reset_student_attempts_for_entrance_exam',
        name="reset_student_attempts_for_entrance_exam"
    ), url(
        r'^rescore_entrance_exam$',
        'instructor.views.api.rescore_entrance_exam',
        name="rescore_entrance_exam"
    ), url(
        r'^list_entrance_exam_instructor_tasks',
        'instructor.views.api.list_entrance_exam_instructor_tasks',
        name="list_entrance_exam_instructor_tasks"
    ), url(
        r'^mark_student_can_skip_entrance_exam',
        'instructor.views.api.mark_student_can_skip_entrance_exam',
        name="mark_student_can_skip_entrance_exam"
    ),

    url(r'^list_instructor_tasks$',
        'instructor.views.api.list_instructor_tasks', name="list_instructor_tasks"),
    url(r'^list_background_email_tasks$',
        'instructor.views.api.list_background_email_tasks', name="list_background_email_tasks"),
    url(r'^list_email_content$',
        'instructor.views.api.list_email_content', name="list_email_content"),
    url(r'^list_forum_members$',
        'instructor.views.api.list_forum_members', name="list_forum_members"),
    url(r'^update_forum_role_membership$',
        'instructor.views.api.update_forum_role_membership', name="update_forum_role_membership"),
    url(r'^send_email$',
        'instructor.views.api.send_email', name="send_email"),
    url(r'^change_due_date$', 'instructor.views.api.change_due_date',
        name='change_due_date'),
    url(r'^reset_due_date$', 'instructor.views.api.reset_due_date',
        name='reset_due_date'),
    url(r'^show_unit_extensions$', 'instructor.views.api.show_unit_extensions',
        name='show_unit_extensions'),
    url(r'^show_student_extensions$', 'instructor.views.api.show_student_extensions',
        name='show_student_extensions'),
    url(r'^irc_instructor_auth_token$', 'instructor.views.api.irc_instructor_auth_token'),

    # proctored exam downloads...
    url(r'^get_proctored_exam_results$',
        'instructor.views.api.get_proctored_exam_results', name="get_proctored_exam_results"),

    # Grade downloads...
    url(r'^list_report_downloads$',
        'instructor.views.api.list_report_downloads', name="list_report_downloads"),
    url(r'calculate_grades_csv$',
        'instructor.views.api.calculate_grades_csv', name="calculate_grades_csv"),
    url(r'problem_grade_report$',
        'instructor.views.api.problem_grade_report', name="problem_grade_report"),

    # Student responses for questions
    url(r'^get_student_responses$',
        'instructor.views.api.get_student_responses', name="get_student_responses"),

    # Financial Report downloads..
    url(r'^list_financial_report_downloads$',
        'instructor.views.api.list_financial_report_downloads', name="list_financial_report_downloads"),

    # Registration Codes..
    url(r'get_registration_codes$',
        'instructor.views.api.get_registration_codes', name="get_registration_codes"),
    url(r'generate_registration_codes$',
        'instructor.views.api.generate_registration_codes', name="generate_registration_codes"),
    url(r'active_registration_codes$',
        'instructor.views.api.active_registration_codes', name="active_registration_codes"),
    url(r'spent_registration_codes$',
        'instructor.views.api.spent_registration_codes', name="spent_registration_codes"),

    # Reports..
    url(r'get_enrollment_report$',
        'instructor.views.api.get_enrollment_report', name="get_enrollment_report"),
    url(r'get_exec_summary_report$',
        'instructor.views.api.get_exec_summary_report', name="get_exec_summary_report"),
    url(r'get_course_survey_results$',
        'instructor.views.api.get_course_survey_results', name="get_course_survey_results"),

    # Coupon Codes..
    url(r'get_coupon_codes',
        'instructor.views.api.get_coupon_codes', name="get_coupon_codes"),

    # spoc gradebook
    url(r'^gradebook$',
        'instructor.views.gradebook_api.spoc_gradebook', name='spoc_gradebook'),

    url(r'^gradebook/(?P<offset>[0-9]+)$',
        'instructor.views.gradebook_api.spoc_gradebook', name='spoc_gradebook'),

    # Blank LTI csv
    url(
        r'^get_blank_lti$',
        'instructor.views.api.get_blank_lti',
        name='get_blank_lti',
    ),

    # Upload LTI csv
    url(
        r'^upload_lti$',
        'instructor.views.api.upload_lti',
        name='upload_lti',
    ),

    # Collect student forums data
    url(r'get_student_forums_usage',
        'instructor.views.api.get_student_forums_usage', name='get_student_forums_usage'),

    # Delete Report Download
    url(r'delete_report_download',
        'instructor.views.api.delete_report_download', name='delete_report_download'),

    # Collect ora2 data
    url(r'get_ora2_responses/(?P<include_email>\w+)/$',
        'instructor.views.api.get_ora2_responses', name="get_ora2_responses"),

    # Collect course forums data
    url(r'get_course_forums_usage',
        'instructor.views.api.get_course_forums_usage', name="get_course_forums_usage"),

    # Generating course forums usage graph
    url(r'^graph_course_forums_usage',
        'instructor.views.api.graph_course_forums_usage', name="graph_course_forums_usage"),

    # Cohort management
    url(r'add_users_to_cohorts$',
        'instructor.views.api.add_users_to_cohorts', name="add_users_to_cohorts"),

    # Certificates
    url(r'^generate_example_certificates$',
        'instructor.views.api.generate_example_certificates',
        name='generate_example_certificates'),

    url(r'^enable_certificate_generation$',
        'instructor.views.api.enable_certificate_generation',
        name='enable_certificate_generation'),

    url(r'^start_certificate_generation',
        'instructor.views.api.start_certificate_generation',
        name='start_certificate_generation'),

    url(r'^start_certificate_regeneration',
        'instructor.views.api.start_certificate_regeneration',
        name='start_certificate_regeneration'),

    url(r'^certificate_exception_view/$',
        'instructor.views.api.certificate_exception_view',
        name='certificate_exception_view'),

    url(r'^generate_certificate_exceptions/(?P<generate_for>[^/]*)',
        'instructor.views.api.generate_certificate_exceptions',
        name='generate_certificate_exceptions'),

    url(r'^generate_bulk_certificate_exceptions',
        'instructor.views.api.generate_bulk_certificate_exceptions',
        name='generate_bulk_certificate_exceptions'),

    url(r'^certificate_invalidation_view/$',
        'instructor.views.api.certificate_invalidation_view',
        name='certificate_invalidation_view'),
)
