"""
List of edx tests to skip, while testing LMS, CMS or lib tests. Pattern for test path is as follows

{path_to_module}.py::{class_name}::{test_name}
"""
# pylint: disable=line-too-long
TEST_SKIP_LIST = [
    'cms/djangoapps/contentstore/tests/test_proctoring.py::TestProctoredExams::test_publishing_exam_1__True__False__True__False__False_',  # noqa: E501
    'cms/djangoapps/contentstore/tests/test_proctoring.py::TestProctoredExams::test_advanced_settings_2__False__True__1_',  # noqa: E501
    'cms/djangoapps/contentstore/tests/test_proctoring.py::TestProctoredExams::test_advanced_settings_1__True__False__1_',  # noqa: E501
    'cms/djangoapps/contentstore/tests/test_tasks.py::ExportCourseTestCase::test_invalid_user_id',
    'cms/djangoapps/contentstore/tests/test_course_settings.py::CourseGradingTest::test_update_grader_from_json',

    'lms/djangoapps/bulk_email/tests/test_email.py::LocalizedFromAddressPlatformLangTestCase::test_english_platform',
    'lms/djangoapps/bulk_email/tests/test_email.py::LocalizedFromAddressPlatformLangTestCase::test_esperanto_platform',
    'lms/djangoapps/bulk_email/tests/test_email.py::LocalizedFromAddressCourseLangTestCase::test_esperanto_platform_arabic_course',  # noqa: E501
    'lms/djangoapps/bulk_email/tests/test_email.py::TestEmailSendFromDashboard::test_unicode_message_send_to_all',
    'lms/djangoapps/commerce/tests/test_signals.py::TestRefundSignal::test_create_zendesk_ticket',
    'lms/djangoapps/courseware/tests/test_video_mongo.py::TestGetHtmlMethod::test_html_student_public_view',
    'lms/djangoapps/courseware/tests/test_video_mongo.py::TestGetHtmlMethod::test_poster_image',
    'lms/djangoapps/courseware/tests/test_video_mongo.py::TestGetHtmlMethod::test_get_html_hls',
    'lms/djangoapps/discussion/django_comment_client/tests/test_utils.py::CategoryMapTestCase::test_self_paced_start_date_filter',  # noqa: E501
    'lms/djangoapps/discussion/django_comment_client/tests/test_utils.py::CategoryMapTestCase::test_sort_intermediates',
    'lms/djangoapps/discussion/django_comment_client/tests/test_utils.py::CategoryMapTestCase::test_tree',
    'lms/djangoapps/discussion/rest_api/tests/test_api.py::GetThreadListTest::test_thread_content',
    'lms/djangoapps/discussion/rest_api/tests/test_serializers.py::ThreadSerializerSerializationTest::test_basic',
    'lms/djangoapps/survey/tests/test_views.py::SurveyViewsTests::test_survey_postback',

    'common/djangoapps/course_modes/tests/test_admin.py::AdminCourseModePageTest::test_expiration_timezone',
    'common/djangoapps/pipeline_mako/tests/test_render.py::RequireJSPathOverridesTest::test_requirejs_path_overrides',
    'common/djangoapps/terrain/stubs/tests/test_xqueue_stub.py::StubXQueueServiceTest::test_grade_request',

    'openedx/core/djangoapps/user_api/accounts/tests/test_retirement_views.py::TestLMSAccountRetirementPost::test_retire_user',  # noqa: E501
    'openedx/core/djangoapps/user_api/accounts/tests/test_retirement_views.py::TestLMSAccountRetirementPost::test_retire_user_twice_idempotent',  # noqa: E501
    'openedx/features/discounts/tests/test_applicability.py::TestApplicability::test_holdback_group_ids_1__0__True_',

    'pavelib/paver_tests/test_extract_and_generate.py::TestGenerate::test_main',
    'pavelib/paver_tests/test_extract_and_generate.py::TestGenerate::test_merge',
]
