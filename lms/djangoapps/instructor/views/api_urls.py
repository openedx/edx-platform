<<<<<<< HEAD
=======

>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
"""
Instructor API endpoint urls.
"""

from django.urls import path, re_path

from lms.djangoapps.instructor.views import api, gradebook_api
from openedx.core.constants import COURSE_ID_PATTERN

# These endpoints are exposing existing views in a way that can be used by MFEs
# or other API clients. They are currently versioned at `v1` since they have
# been around without major changes for a while and will probably not be changed
# in incompatible ways. If they do need incompatible changes for use via MFEs
# then new v2 endpoints can be introduced.
v1_api_urls = [
    re_path(rf'^tasks/{COURSE_ID_PATTERN}$', api.InstructorTasks.as_view(), name='list_instructor_tasks', ),
    re_path(rf'^reports/{COURSE_ID_PATTERN}$', api.ReportDownloads.as_view(), name='list_report_downloads', ),
    re_path(rf'^reports/{COURSE_ID_PATTERN}/generate/problem_responses$', api.ProblemResponseReportInitiate.as_view(),
            name='generate_problem_responses', ),
]

urlpatterns = [
    path('students_update_enrollment', api.students_update_enrollment, name='students_update_enrollment'),
<<<<<<< HEAD
    path('register_and_enroll_students', api.register_and_enroll_students, name='register_and_enroll_students'),
    path('list_course_role_members', api.list_course_role_members, name='list_course_role_members'),
    path('modify_access', api.modify_access, name='modify_access'),
    path('bulk_beta_modify_access', api.bulk_beta_modify_access, name='bulk_beta_modify_access'),
    path('get_problem_responses', api.get_problem_responses, name='get_problem_responses'),
    path('get_grading_config', api.get_grading_config, name='get_grading_config'),
    re_path(r'^get_students_features(?P<csv>/csv)?$', api.get_students_features, name='get_students_features'),
    path('get_issued_certificates/', api.get_issued_certificates, name='get_issued_certificates'),
    path('get_students_who_may_enroll', api.get_students_who_may_enroll, name='get_students_who_may_enroll'),
    path('get_anon_ids', api.get_anon_ids, name='get_anon_ids'),
    path('get_student_enrollment_status', api.get_student_enrollment_status, name="get_student_enrollment_status"),
    path('get_student_progress_url', api.get_student_progress_url, name='get_student_progress_url'),
    path('reset_student_attempts', api.reset_student_attempts, name='reset_student_attempts'),
=======
    path('register_and_enroll_students', api.RegisterAndEnrollStudents.as_view(), name='register_and_enroll_students'),
    path('list_course_role_members', api.ListCourseRoleMembersView.as_view(), name='list_course_role_members'),
    path('modify_access', api.ModifyAccess.as_view(), name='modify_access'),
    path('bulk_beta_modify_access', api.bulk_beta_modify_access, name='bulk_beta_modify_access'),
    path('get_problem_responses', api.get_problem_responses, name='get_problem_responses'),
    path('get_issued_certificates/', api.GetIssuedCertificates.as_view(), name='get_issued_certificates'),
    re_path(r'^get_students_features(?P<csv>/csv)?$', api.GetStudentsFeatures.as_view(), name='get_students_features'),
    path('get_grading_config', api.GetGradingConfig.as_view(), name='get_grading_config'),
    path('get_students_who_may_enroll', api.GetStudentsWhoMayEnroll.as_view(), name='get_students_who_may_enroll'),
    path('get_anon_ids', api.GetAnonIds.as_view(), name='get_anon_ids'),
    path('get_student_enrollment_status', api.GetStudentEnrollmentStatus.as_view(),
         name="get_student_enrollment_status"),
    path('get_student_progress_url', api.StudentProgressUrl.as_view(), name='get_student_progress_url'),
    path('reset_student_attempts', api.ResetStudentAttempts.as_view(), name='reset_student_attempts'),
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    path('rescore_problem', api.rescore_problem, name='rescore_problem'),
    path('override_problem_score', api.override_problem_score, name='override_problem_score'),
    path('reset_student_attempts_for_entrance_exam', api.reset_student_attempts_for_entrance_exam,
         name='reset_student_attempts_for_entrance_exam'),
    path('rescore_entrance_exam', api.rescore_entrance_exam, name='rescore_entrance_exam'),
<<<<<<< HEAD
    path('list_entrance_exam_instructor_tasks', api.list_entrance_exam_instructor_tasks,
         name='list_entrance_exam_instructor_tasks'),
    path('mark_student_can_skip_entrance_exam', api.mark_student_can_skip_entrance_exam,
         name='mark_student_can_skip_entrance_exam'),
    path('list_instructor_tasks', api.list_instructor_tasks, name='list_instructor_tasks'),
    path('list_background_email_tasks', api.list_background_email_tasks, name='list_background_email_tasks'),
    path('list_email_content', api.list_email_content, name='list_email_content'),
    path('list_forum_members', api.list_forum_members, name='list_forum_members'),
    path('update_forum_role_membership', api.update_forum_role_membership, name='update_forum_role_membership'),
    path('send_email', api.send_email, name='send_email'),
    path('change_due_date', api.change_due_date, name='change_due_date'),
    path('reset_due_date', api.reset_due_date, name='reset_due_date'),
    path('show_unit_extensions', api.show_unit_extensions, name='show_unit_extensions'),
    path('show_student_extensions', api.show_student_extensions, name='show_student_extensions'),
=======
    path('list_entrance_exam_instructor_tasks', api.ListEntranceExamInstructorTasks.as_view(),
         name='list_entrance_exam_instructor_tasks'),
    path('mark_student_can_skip_entrance_exam', api.MarkStudentCanSkipEntranceExam.as_view(),
         name='mark_student_can_skip_entrance_exam'),
    path('list_instructor_tasks', api.ListInstructorTasks.as_view(), name='list_instructor_tasks'),
    path('list_background_email_tasks', api.list_background_email_tasks, name='list_background_email_tasks'),
    path('list_email_content', api.ListEmailContent.as_view(), name='list_email_content'),
    path('list_forum_members', api.list_forum_members, name='list_forum_members'),
    path('update_forum_role_membership', api.update_forum_role_membership, name='update_forum_role_membership'),
    path('change_due_date', api.ChangeDueDate.as_view(), name='change_due_date'),
    path('send_email', api.SendEmail.as_view(), name='send_email'),
    path('reset_due_date', api.ResetDueDate.as_view(), name='reset_due_date'),
    path('show_unit_extensions', api.show_unit_extensions, name='show_unit_extensions'),
    path('show_student_extensions', api.ShowStudentExtensions.as_view(), name='show_student_extensions'),
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    # proctored exam downloads...
    path('get_proctored_exam_results', api.get_proctored_exam_results, name='get_proctored_exam_results'),

    # Grade downloads...
<<<<<<< HEAD
    path('list_report_downloads', api.list_report_downloads, name='list_report_downloads'),
=======
    path('list_report_downloads', api.ListReportDownloads.as_view(), name='list_report_downloads'),
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    path('calculate_grades_csv', api.calculate_grades_csv, name='calculate_grades_csv'),
    path('problem_grade_report', api.problem_grade_report, name='problem_grade_report'),

    # Reports..
    path('get_course_survey_results', api.get_course_survey_results, name='get_course_survey_results'),
    path('export_ora2_data', api.export_ora2_data, name='export_ora2_data'),
    path('export_ora2_summary', api.export_ora2_summary, name='export_ora2_summary'),

    path('export_ora2_submission_files', api.export_ora2_submission_files,
         name='export_ora2_submission_files'),

    # spoc gradebook
    path('gradebook', gradebook_api.spoc_gradebook, name='spoc_gradebook'),

    path('gradebook/<int:offset>', gradebook_api.spoc_gradebook, name='spoc_gradebook'),

    # Cohort management
    path('add_users_to_cohorts', api.add_users_to_cohorts, name='add_users_to_cohorts'),

    # Certificates
    path('enable_certificate_generation', api.enable_certificate_generation, name='enable_certificate_generation'),
<<<<<<< HEAD
    path('start_certificate_generation', api.start_certificate_generation, name='start_certificate_generation'),
=======
    path('start_certificate_generation', api.StartCertificateGeneration.as_view(), name='start_certificate_generation'),
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    path('start_certificate_regeneration', api.start_certificate_regeneration, name='start_certificate_regeneration'),
    path('certificate_exception_view/', api.certificate_exception_view, name='certificate_exception_view'),
    re_path(r'^generate_certificate_exceptions/(?P<generate_for>[^/]*)', api.generate_certificate_exceptions,
            name='generate_certificate_exceptions'),
    path('generate_bulk_certificate_exceptions', api.generate_bulk_certificate_exceptions,
         name='generate_bulk_certificate_exceptions'),
<<<<<<< HEAD
    path('certificate_invalidation_view/', api.certificate_invalidation_view, name='certificate_invalidation_view'),
=======
    path(
        'certificate_invalidation_view/',
        api.CertificateInvalidationView.as_view(),
        name='certificate_invalidation_view'
    ),
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
]
