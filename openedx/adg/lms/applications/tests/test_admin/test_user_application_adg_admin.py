"""
Tests for all functionality related to UserApplicationADGAdmin
"""
# pylint: disable=protected-access

import mock
import pytest
from django.contrib.auth.models import Group
from django.utils.html import format_html

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.constants import MONTH_DAY_YEAR_FORMAT
from openedx.adg.lms.applications.admin import UserApplicationADGAdmin
from openedx.adg.lms.applications.constants import (
    ACCEPTED_APPLICATIONS_TITLE,
    ALL_APPLICATIONS_TITLE,
    APPLICANT_INFO,
    APPLYING_TO,
    BACKGROUND_QUESTION,
    BACKGROUND_QUESTION_TITLE,
    DATE_OF_BIRTH,
    DAY_MONTH_YEAR_FORMAT,
    EMAIL,
    EMAIL_ADDRESS_HTML_FORMAT,
    GENDER,
    GENDER_MAP,
    HEAR_ABOUT_OMNI,
    INTEREST,
    INTEREST_IN_BUSINESS,
    IS_SAUDI_NATIONAL,
    LINKED_IN_PROFILE,
    LINKED_IN_PROFILE_HTML_FORMAT,
    LOCATION,
    OPEN_APPLICATIONS_TITLE,
    ORGANIZATION,
    PHONE_NUMBER,
    PREREQUISITES,
    SCORES,
    STATUS_PARAM,
    WAITLISTED_APPLICATIONS_TITLE
)
from openedx.adg.lms.applications.models import ApplicationHub, UserApplication
from openedx.adg.lms.applications.tests.constants import (
    ADMIN_TYPE_ADG_ADMIN,
    ADMIN_TYPE_SUPER_ADMIN,
    ALL_FIELDSETS,
    FORMSET,
    LINKED_IN_URL,
    NOTE,
    TEST_BACKGROUND_QUESTION,
    TEST_HEAR_ABOUT_OMNI,
    TEST_INTEREST_IN_BUSINESS,
    TEST_MESSAGE_FOR_APPLICANT,
    TITLE_BUSINESS_LINE_1,
    TITLE_BUSINESS_LINE_2
)
from openedx.adg.lms.applications.tests.factories import ApplicationHubFactory, WorkExperienceFactory
from openedx.adg.lms.registration_extension.tests.factories import ExtendedUserProfileFactory


@pytest.mark.django_db
@pytest.mark.parametrize(
    'admin_type', [
        ADMIN_TYPE_SUPER_ADMIN,
        ADMIN_TYPE_ADG_ADMIN,
    ], ids=[ADMIN_TYPE_SUPER_ADMIN, ADMIN_TYPE_ADG_ADMIN]
)
@mock.patch('openedx.adg.lms.applications.admin.UserApplication.submitted_applications')
def test_get_queryset_with_super_admin_and_adg_admin(
    mock_submitted_applications_manager, admin_user, user_applications_with_different_business_lines, request
):
    """
    Test that `get_queryset()` returns all submitted applications for super admins and ADG Admins.
    """
    mock_submitted_applications_manager.all.return_value = user_applications_with_different_business_lines
    request.user = admin_user

    assert UserApplicationADGAdmin.get_queryset('self', request) == user_applications_with_different_business_lines


@pytest.mark.django_db
@pytest.mark.parametrize(
    'business_line_title', [
        TITLE_BUSINESS_LINE_1,
        TITLE_BUSINESS_LINE_2,
    ], ids=[TITLE_BUSINESS_LINE_1, TITLE_BUSINESS_LINE_2]
)
@mock.patch('openedx.adg.lms.applications.admin.UserApplication.submitted_applications')
def test_get_queryset_with_bu_admins(
    mock_submitted_applications_manager,
    business_line_title,
    user_applications_with_different_business_lines,
    request
):
    """
    Test that `get_queryset()` returns only the applications of the particular business line, for business line admins
    """
    mock_submitted_applications_manager.all.return_value = user_applications_with_different_business_lines
    request.user = UserFactory(is_staff=True, groups=[Group.objects.filter(name=business_line_title).first()])

    assert len(UserApplicationADGAdmin.get_queryset('self', request)) == 1
    assert UserApplicationADGAdmin.get_queryset('self', request).first().business_line.title == business_line_title


@pytest.mark.django_db
def test_applicant_name(user_application):
    """
    Test that `applicant_name()` field method returns the user's full name from user
    profile.
    """
    expected_name = user_application.user.profile.name
    actual_name = UserApplicationADGAdmin.applicant_name('self', user_application)

    assert expected_name == actual_name


@pytest.mark.django_db
def test_date_received(user_application, current_date):
    """
    Test that `date_received()` field method returns submission date of the application in the correct format
    (MM/DD/YYYY).
    """
    application_hub = ApplicationHubFactory()
    application_hub.user = user_application.user

    application_hub.submission_date = current_date

    expected_date = current_date.strftime(MONTH_DAY_YEAR_FORMAT)
    actual_date = UserApplicationADGAdmin.date_received('self', user_application)

    assert expected_date == actual_date


@pytest.mark.parametrize(
    'status, expected_title', [
        (None, ALL_APPLICATIONS_TITLE),
        (UserApplication.OPEN, OPEN_APPLICATIONS_TITLE),
        (UserApplication.WAITLIST, WAITLISTED_APPLICATIONS_TITLE),
        (UserApplication.ACCEPTED, ACCEPTED_APPLICATIONS_TITLE)
    ], ids=['all_applications', 'open_applications', 'waitlisted_applications', 'accepted_applications']
)
@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.admin.admin.ModelAdmin.changelist_view')
def test_changelist_view(
    mock_changelist_view, request, user_application, user_application_adg_admin_instance, status, expected_title
):
    """
    Test that the correct title is passed in context for the application listing page view, based on the status filter
    selected by the admin.
    """
    request.GET = {}
    if status:
        request.GET[STATUS_PARAM] = status

    UserApplicationADGAdmin.changelist_view(user_application_adg_admin_instance, request)

    expected_context = {'title': expected_title}
    mock_changelist_view.assert_called_once_with(request, extra_context=expected_context)


@pytest.mark.parametrize(
    'request_method', ['GET', 'POST'], ids=['get', 'post_without_status']
)
@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.admin.admin.ModelAdmin.changeform_view')
@mock.patch('openedx.adg.lms.applications.admin.get_extra_context_for_application_review_page')
@mock.patch('openedx.adg.lms.applications.admin.UserApplicationADGAdmin._save_application_review_info')
@mock.patch('openedx.adg.lms.applications.admin.UserApplicationADGAdmin._send_application_status_update_email')
def test_changeform_view(
    mock_send_application_status_update_email,
    mock_save_application_review_info,
    mock_get_extra_context_for_application_review_page,
    mock_changeform_view,
    request,
    user_application,
    user_application_adg_admin_instance,
    request_method,
    mocker
):
    """
    Test the overridden changeform_view.

    Test Case 1: get
        Test that if a GET request is made, the right context should be rendered for the application review page.

    Test Case 2: post_without_status
        Test that if a POST request is made with an internal note but without status, the application should not be
        saved and the right context should be rendered for the application review page.
    """
    mocker.patch.object(ApplicationHub.objects, 'get')

    application_id = user_application.id

    expected_context = {'test_key': 'test_value'}
    mock_get_extra_context_for_application_review_page.return_value = expected_context

    request.method = request_method
    if request.method == 'POST':
        request.POST = {'internal_note': NOTE}

    UserApplicationADGAdmin.changeform_view(user_application_adg_admin_instance, request, application_id)

    mock_save_application_review_info.assert_not_called()
    mock_send_application_status_update_email.assert_not_called()
    mock_get_extra_context_for_application_review_page.assert_called_once_with(user_application)
    mock_changeform_view.assert_called_once_with(request, application_id, extra_context=expected_context)


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.admin.admin.ModelAdmin.changeform_view')
@mock.patch('openedx.adg.lms.applications.admin.UserApplicationADGAdmin._save_application_review_info')
@mock.patch('openedx.adg.lms.applications.admin.UserApplicationADGAdmin._send_application_status_update_email')
def test_changeform_view_post_with_status(
    mock_send_application_status_update_email,
    mock_save_application_review_info,
    mock_changeform_view,
    request,
    user_application,
    user_application_adg_admin_instance,
):
    """
    Test the overridden changeform_view.

    Test that if a POST request is made with internal note and status, the application should be updated, saved and
    an application status email should be sent to the applicant.
    """
    application_id = user_application.id

    request.method = 'POST'
    request.POST = {
        'internal_note': NOTE,
        'status': 'test_status',
        'message_for_applicant': TEST_MESSAGE_FOR_APPLICANT
    }
    UserApplicationADGAdmin.changeform_view(user_application_adg_admin_instance, request, application_id)

    mock_save_application_review_info.assert_called_once_with(user_application, request, NOTE)
    mock_send_application_status_update_email.assert_called_once_with(user_application, TEST_MESSAGE_FOR_APPLICANT)
    mock_changeform_view.assert_called_once_with(request, application_id, extra_context=None)


@pytest.mark.django_db
def test_save_application_review_info(request, user_application):
    """
    Test that application review information is successfully saved.
    """
    request.user = UserFactory()
    request.POST = {'status': UserApplication.ACCEPTED}

    UserApplicationADGAdmin._save_application_review_info('self', user_application, request, NOTE)

    updated_application = UserApplication.objects.get(id=user_application.id)

    assert updated_application.status == UserApplication.ACCEPTED
    assert updated_application.internal_admin_note == NOTE
    assert updated_application.reviewed_by == request.user


@pytest.mark.django_db
@pytest.mark.parametrize(
    'status, expected_email_template', [
        (UserApplication.WAITLIST, MandrillClient.APPLICATION_WAITLISTED),
        (UserApplication.ACCEPTED, MandrillClient.APPLICATION_ACCEPTED)
    ], ids=['wait_list', 'accepted']
)
@mock.patch('openedx.adg.lms.applications.admin.get_user_first_name', return_value='test')
@mock.patch('openedx.adg.lms.applications.admin.MandrillClient.__init__', return_value=None)
@mock.patch('openedx.adg.lms.applications.admin.task_send_mandrill_email')
def test_send_application_status_update_email(
    mock_send_mandrill_email, mock_init, mock_get_first_name, status, expected_email_template, request, user_application
):
    """
     Test that upon application status update, applicant is intimated via an email with correct template and context.
    """
    request.method = 'POST'
    user_application.status = status

    expected_email_context = {
        'first_name': mock_get_first_name(),
        'message_for_applicant': TEST_MESSAGE_FOR_APPLICANT,
    }

    UserApplicationADGAdmin._send_application_status_update_email('self', user_application, TEST_MESSAGE_FOR_APPLICANT)
    mock_send_mandrill_email.delay.assert_called_once_with(
        expected_email_template, [user_application.user.email], expected_email_context
    )


@pytest.mark.django_db
def test_email(user_application):
    """
    Test that the `email` field method returns safe HTML containing the correct email address of the applicant.
    """
    expected_email_address = format_html(EMAIL_ADDRESS_HTML_FORMAT, email_address=user_application.user.email)
    actual_email_address = UserApplicationADGAdmin.email('self', user_application)

    assert expected_email_address == actual_email_address


@pytest.mark.parametrize(
    'country, expected_location', [
        (None, 'Test_city'),
        ('Test_country', 'Test_city, Test_country')
    ]
)
@pytest.mark.django_db
def test_location(user_application, country, expected_location):
    """
    Test that the `location` field method returns city and conditionally, country of the applicant.
    """
    user_profile = user_application.user.profile
    user_profile.city = 'Test_city'
    user_profile.country = country

    actual_location = UserApplicationADGAdmin.location('self', user_application)

    assert expected_location == actual_location


@pytest.mark.django_db
def test_linked_in_profile(user_application):
    """
    Test that the `linked_in_profile` field method returns safe HTML containing link of the applicant's LinkedIn profile
    """
    user_application.linkedin_url = LINKED_IN_URL

    expected_linked_in_profile = format_html(LINKED_IN_PROFILE_HTML_FORMAT, url='Test LinkedIn URL')
    actual_linked_in_profile = UserApplicationADGAdmin.linked_in_profile('self', user_application)

    assert expected_linked_in_profile == actual_linked_in_profile


@pytest.mark.parametrize(
    'saudi_national, expected_answer', [
        (True, 'Yes'),
        (False, 'No')
    ]
)
@pytest.mark.django_db
def test_is_saudi_national(user_application, saudi_national, expected_answer):
    """
    Test that if the applicant is a Saudi national, `is_saudi_national` field method should return 'Yes'; 'No' otherwise
    """
    extended_profile = ExtendedUserProfileFactory(user=user_application.user)
    extended_profile.saudi_national = saudi_national

    actual_answer = UserApplicationADGAdmin.is_saudi_national('self', user_application)

    assert expected_answer == actual_answer


@pytest.mark.parametrize(
    'gender_choice, expected_gender', [
        (choice, gender) for choice, gender in GENDER_MAP.items()  # pylint: disable=unnecessary-comprehension
    ], ids=['male', 'female', 'other']
)
@pytest.mark.django_db
def test_gender(user_application, gender_choice, expected_gender):
    """
    Test that the `gender` field method returns the gender chosen by the applicant.
    """
    user_profile = user_application.user.profile
    user_profile.gender = gender_choice

    actual_gender = UserApplicationADGAdmin.gender('self', user_application)

    assert expected_gender == actual_gender


@pytest.mark.django_db
def test_phone_number(user_application):
    """
    Test that the `phone_number` field method returns the phone number of the applicant.
    """
    user_profile = user_application.user.profile
    user_profile.phone_number = 'Test Phone Number'

    expected_phone_number = user_profile.phone_number
    actual_phone_number = UserApplicationADGAdmin.phone_number('self', user_application)

    assert expected_phone_number == actual_phone_number


@pytest.mark.django_db
def test_date_of_birth(user_application, current_date):
    """
    Test the the `date_of_birth` field method returns the birth date of the applicant in the correct format.
    """
    extended_profile = ExtendedUserProfileFactory(user=user_application.user)
    extended_profile.birth_date = current_date

    expected_date_of_birth = extended_profile.birth_date.strftime(DAY_MONTH_YEAR_FORMAT)
    actual_date_of_birth = UserApplicationADGAdmin.date_of_birth('self', user_application)

    assert expected_date_of_birth == actual_date_of_birth


@pytest.mark.django_db
def test_applying_to(user_application):
    """
    Test that the `applying_to` field method returns the business line that the applicant is applying to.
    """
    expected_business_line = user_application.business_line
    actual_business_line = UserApplicationADGAdmin.applying_to('self', user_application)

    assert expected_business_line == actual_business_line


@pytest.mark.django_db
def test_hear_about_omni(user_application):
    """
    Test that the `hear_about_omni` field method returns the added text in the field, if
    any, for the applicant
    """
    extended_profile = ExtendedUserProfileFactory(user=user_application.user)
    extended_profile.hear_about_omni = TEST_HEAR_ABOUT_OMNI
    actual_hear_about_omni_value = UserApplicationADGAdmin.hear_about_omni('self', user_application)

    assert TEST_HEAR_ABOUT_OMNI == actual_hear_about_omni_value


@pytest.mark.django_db
def test_prerequisites(user_application, mocker):
    """
    Test that the `prerequisites` field method returns safe and correct HTML for scores of applicant in prereq courses.
    """
    dummy_html = 'Dummy html string'
    mocker.patch(
        'openedx.adg.lms.applications.admin.create_html_string_for_course_scores_in_admin_review',
        return_value=dummy_html
    )
    actual_result = UserApplicationADGAdmin.prerequisites('self', user_application)
    assert actual_result == dummy_html


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.admin.UserApplicationADGAdmin._get_fieldset_for_scores')
@mock.patch('openedx.adg.lms.applications.admin.UserApplicationADGAdmin._get_fieldset_for_interest')
@mock.patch('openedx.adg.lms.applications.admin.UserApplicationADGAdmin._get_applicant_info_fieldset')
@mock.patch('openedx.adg.lms.applications.admin.UserApplicationADGAdmin._get_fieldset_for_background_question')
@mock.patch('openedx.adg.lms.applications.admin.UserApplicationADGAdmin._get_preliminary_info_fieldset')
def test_get_fieldsets(
    mock_get_preliminary_info_fieldset,
    mock_get_fieldset_for_background_question,
    mock_get_applicant_info_fieldset,
    mock_get_fieldset_for_interest,
    mock_get_fieldset_for_scores,
    request,
    user_application,
    user_application_adg_admin_instance
):
    """
    Test that the `get_fieldsets` method gets the fieldsets for: preliminary info, applicant info,
    background_question, interest, and scores of applicant.

    """
    mock_get_preliminary_info_fieldset.return_value = ALL_FIELDSETS[0]
    mock_get_applicant_info_fieldset.return_value = ALL_FIELDSETS[1]
    mock_get_fieldset_for_interest.return_value = ALL_FIELDSETS[3]
    mock_get_fieldset_for_scores.return_value = ALL_FIELDSETS[4]
    mock_get_fieldset_for_background_question.return_value = ALL_FIELDSETS[2]

    user_application.interest_in_business = TEST_INTEREST_IN_BUSINESS
    user_application.background_question = TEST_BACKGROUND_QUESTION

    actual_fieldsets = UserApplicationADGAdmin.get_fieldsets(
        user_application_adg_admin_instance, request, user_application
    )

    assert actual_fieldsets == ALL_FIELDSETS


@pytest.mark.parametrize('linkedin_url, expected_fields', [
    (LINKED_IN_URL, (EMAIL, LOCATION, LINKED_IN_PROFILE)),
    (None, (EMAIL, LOCATION))
], ids=['with_linkedIn profile', 'without_linkedIn_profile'])
@pytest.mark.django_db
def test_get_preliminary_info_fieldset(user_application, linkedin_url, expected_fields):
    """
    Test that the `_get_preliminary_info_fieldset` method returns the correct fieldset.

    Fieldset title should be empty and email, location and conditionally LinkedIn profile of the applicant should be
    returned as fields in the fieldset.
    """
    user_application.linkedin_url = linkedin_url

    expected_fieldset = ('', {'fields': expected_fields})
    actual_fieldset = UserApplicationADGAdmin._get_preliminary_info_fieldset('self', user_application)

    assert expected_fieldset == actual_fieldset


@pytest.mark.parametrize(
    'organization', [None, 'Test_organization']
)
@pytest.mark.django_db
def test_get_applicant_info_fieldset(user_application, organization):
    """
    Test that the `_get_applicant_info_fieldset` method returns the correct fieldset for both cases, i.e. when
    organization is:
        1. provided in the application
        2. not provided in the application
    """
    expected_fields = [IS_SAUDI_NATIONAL, GENDER, PHONE_NUMBER, DATE_OF_BIRTH]

    user_application.organization = organization
    if organization:
        expected_fields.append(ORGANIZATION)

    expected_fields.extend([APPLYING_TO, HEAR_ABOUT_OMNI])

    expected_fieldset = (APPLICANT_INFO, {'fields': tuple(expected_fields)})
    actual_fieldset = UserApplicationADGAdmin._get_applicant_info_fieldset('self', user_application)

    assert expected_fieldset == actual_fieldset


@pytest.mark.django_db
def test_get_fieldset_for_interest(user_application, user_application_adg_admin_instance):
    """
    Test that the `_get_fieldset_for_interest` method returns the correct fieldset.
    """
    user_application.interest_in_business = TEST_INTEREST_IN_BUSINESS

    actual_fieldset = UserApplicationADGAdmin._get_fieldset_for_interest(user_application_adg_admin_instance)

    expected_fieldset = (INTEREST, {'fields': (INTEREST_IN_BUSINESS,)})

    assert actual_fieldset == expected_fieldset


@pytest.mark.django_db
def test_get_fieldset_for_background_question(user_application, user_application_adg_admin_instance):
    """
    Test that the `_get_fieldset_for_background_question` method returns the correct fieldset.
    """
    user_application.background_question = TEST_BACKGROUND_QUESTION

    actual_fieldset = UserApplicationADGAdmin._get_fieldset_for_background_question(user_application_adg_admin_instance)

    expected_fieldset = (BACKGROUND_QUESTION_TITLE, {'fields': (BACKGROUND_QUESTION,)})

    assert actual_fieldset == expected_fieldset


def test_get_fieldset_for_scores():
    """
    Test that the `_get_fieldset_for_scores` method returns the correct fieldset.
    """
    expected_fieldset = (SCORES, {'fields': (PREREQUISITES,)})
    actual_fieldset = UserApplicationADGAdmin._get_fieldset_for_scores('self')

    assert expected_fieldset == actual_fieldset


def _mock_get_formsets_with_inlines_dependencies(mocker, education_inline, work_experience_inline):
    """
    Mock all dependencies of the generator function 'get_formsets_with_inlines' at module level.
    """
    mocker.patch(
        'openedx.adg.lms.applications.admin.UserApplicationADGAdmin.get_inline_instances',
        return_value=[education_inline, work_experience_inline]
    )
    mocker.patch(
        'openedx.adg.lms.applications.admin.ApplicationReviewInline.get_formset',
        return_value=FORMSET
    )


@pytest.mark.django_db
def test_get_formsets_with_inlines_no_experience(
    user_application,
    user_application_adg_admin_instance,
    education_inline,
    work_experience_inline,
    mocker
):
    """
    Test that the overridden generator function `get_formsets_with_inlines` yields formset for
    only education in case of no work experience.
    """
    _mock_get_formsets_with_inlines_dependencies(mocker, education_inline, work_experience_inline)

    actual_formsets = UserApplicationADGAdmin.get_formsets_with_inlines(
        user_application_adg_admin_instance, 'request', user_application
    )

    assert next(actual_formsets) == (FORMSET, education_inline)
    with pytest.raises(StopIteration):
        next(actual_formsets)


@pytest.mark.django_db
def test_get_formsets_with_inlines_with_experience(
    user_application,
    user_application_adg_admin_instance,
    education_inline,
    work_experience_inline,
    mocker
):
    """
    Test that the overridden generator function `get_formsets_with_inlines` yields formsets for both education and work
    experience in case the applicant has provided work experience.
    """
    _mock_get_formsets_with_inlines_dependencies(mocker, education_inline, work_experience_inline)

    work_experience = WorkExperienceFactory()
    work_experience.user_application = user_application
    work_experience.save()

    actual_formsets = UserApplicationADGAdmin.get_formsets_with_inlines(
        user_application_adg_admin_instance, 'request', user_application
    )

    assert next(actual_formsets) == (FORMSET, education_inline)
    assert next(actual_formsets) == (FORMSET, work_experience_inline)


@pytest.mark.django_db
def test_get_form(user_application_adg_admin_instance, user_application, request):
    """
    Test that the `get_form` method returns a form with a request object attached.
    """
    admin_form_class = UserApplicationADGAdmin.get_form(user_application_adg_admin_instance, request, user_application)
    admin_form = admin_form_class()

    assert admin_form.request == request


def test_has_delete_permission():
    """
    Test that ADG admin is not allowed to delete an existing user application.
    """
    assert UserApplicationADGAdmin.has_delete_permission('self', 'request') is False


def test_has_add_permission():
    """
    Test that ADG admin is not allowed to add/create a new user application.
    """
    assert UserApplicationADGAdmin.has_add_permission('self', 'request') is False
