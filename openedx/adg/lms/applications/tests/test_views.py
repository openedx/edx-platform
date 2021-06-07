"""
Tests for all the views in applications app.
"""
import mock
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory
from django.urls import reverse
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.lms.applications.views import (
    ApplicationHubView,
    ApplicationIntroductionView,
    ContactInformationView,
    CoverLetterView,
    EducationAndExperienceView
)
from openedx.adg.lms.registration_extension.tests.factories import ExtendedUserProfileFactory

from .constants import COVER_LETTER_REDIRECT_URL, PASSWORD, USERNAME
from .factories import ApplicationHubFactory, BusinessLineFactory, UserApplicationFactory


@pytest.mark.django_db
@pytest.fixture(name='user')
def user_fixture():
    """
    Create a test user and their corresponding ApplicationHub object

    Returns:
        User object
    """
    user = UserFactory(username=USERNAME, password=PASSWORD)
    ApplicationHubFactory(user=user)
    ExtendedUserProfileFactory(user=user)
    return user


@pytest.mark.django_db
@pytest.fixture(name='user_with_no_hub')
def user_with_no_hub_fixture():
    """
    Create a test user with extended profile and without corresponding ApplicationHub object

    Returns:
        User object
    """
    user = UserFactory(username=USERNAME, password=PASSWORD)
    ExtendedUserProfileFactory(user=user)
    return user


@pytest.fixture(scope='module', name='request_factory')
def request_factory_fixture():
    """
    Returns the request factory to make requests.

    Returns:
         RequestFactory object
    """
    return RequestFactory()


@pytest.fixture(name='application_hub_view_get_request')
def application_hub_view_get_request_fixture(request_factory, user_with_no_hub):
    """
    Return a HttpRequest object for application hub get

    Args:
        request_factory (RequestFactory): factory to make requests
        user_with_no_hub (User): The user that is logged in

    Returns:
        HttpRequest object
    """
    request = request_factory.get(reverse('application_hub'))
    request.user = user_with_no_hub
    return request


@pytest.fixture(name='logged_in_client')
def logged_in_client_fixture(user):
    """
    Return a logged in client

    Args:
        user (User): user to log in

    Returns:
        Client() object with logged in user
    """
    client = Client()
    client.login(username=user.username, password=PASSWORD)
    return client


# ------- Application Introduction View tests below -------


@pytest.mark.django_db
def test_get_redirects_without_login_for_application_introduction_view():
    """
    Test the case where an unauthenticated user is redirected to login page or not.
    """
    application_introduction_url = reverse('application_introduction')
    response = Client().get(application_introduction_url)
    assert f'/register?next={application_introduction_url}' == response.url


@pytest.mark.django_db
@pytest.mark.parametrize('application_hub, status_code, expected_output', [
    (True, 302, reverse('application_hub')),
    (False, 200, None)
])
def test_application_introduction_view_for_logged_in_user(
    application_hub, status_code, expected_output, request_factory, mocker
):
    """
    Test that Application Introduction view is only accessible to users that have no ApplicationHub object i.e have not
    clicked the `Start Application` button on Application Introduction page
    """
    mocker.patch('openedx.adg.lms.applications.views.render')

    test_user = UserFactory()
    request = request_factory.get(reverse('application_introduction'))
    request.user = test_user

    if application_hub:
        ApplicationHubFactory(user=test_user)

    response = ApplicationIntroductionView.as_view()(request)
    assert response.get('Location') == expected_output
    assert response.status_code == status_code


@pytest.mark.django_db
@pytest.mark.parametrize(
    'application_hub, status_code, expected_output',
    [
        (False, 302, reverse('application_hub')),
        (True, 400, None)
    ],
    ids=['has_application_hub_object', 'no_application_hub_object']
)
def test_post_request_application_introduction_view(application_hub, status_code, expected_output, request_factory):
    """
    Test post request to application introduction view before and after starting the application
    """
    user = UserFactory()
    request = request_factory.post(reverse('application_introduction'))
    request.user = user

    if application_hub:
        ApplicationHubFactory(user=user)

    response = ApplicationIntroductionView.as_view()(request)

    assert response.get('Location') == expected_output
    assert response.status_code == status_code


# ------- Application Hub View tests below -------


@pytest.mark.django_db
def test_get_redirects_without_login_for_application_hub_view():
    """
    Test the case where an unauthenticated user is redirected to login page or not.
    """
    application_hub_url = reverse('application_hub')
    response = Client().get(application_hub_url)
    assert f'/login?next={application_hub_url}' == response.url


@pytest.mark.django_db
def test_post_user_redirects_without_login_for_application_hub_view():
    """
    Test the case where an unauthenticated user is redirected to login page or not.
    """
    application_hub_url = reverse('application_hub')
    response = Client().post(application_hub_url)
    assert f'/login?next={application_hub_url}' == response.url


@pytest.mark.django_db
def test_application_hub_view_get_request(application_hub_view_get_request):
    """
    Test the case where a user sends get request to application hub with no saved ApplicationHub object.
    """
    response = ApplicationHubView.as_view()(application_hub_view_get_request)

    assert response.get('Location') == reverse('application_introduction')
    assert response.status_code == 302


@pytest.mark.django_db
@pytest.mark.parametrize(
    'has_application_hub_object',
    [False, True],
    ids=['no_application_hub_object', 'has_application_hub_object'])
def test_application_hub_view_post_request(has_application_hub_object, request_factory, user_with_no_hub):
    """
    Test post request to application hub when a user has no saved ApplicationHub object and when a user has a saved
    ApplicationHub object.
    """
    request = request_factory.post(reverse('application_hub'))
    request.user = user_with_no_hub

    if has_application_hub_object:
        ApplicationHubFactory(user=user_with_no_hub)

    response = ApplicationHubView.as_view()(request)

    assert response.status_code == 400


@pytest.mark.django_db
def test_get_initial_application_state_for_application_hub_view(application_hub_view_get_request, mocker):
    """
    Test the case where the user has not completed even a single objective of the application.
    """
    mocker.patch('openedx.adg.lms.applications.views.get_application_hub_instructions', return_value={})
    mock_render = mocker.patch('openedx.adg.lms.applications.views.render')

    ApplicationHubFactory(user=application_hub_view_get_request.user)
    ApplicationHubView.as_view()(application_hub_view_get_request)

    expected_context = {
        'user_application_hub': application_hub_view_get_request.user.application_hub,
        'pre_req_courses': [],
        'business_line_courses': [],
        'is_locked': False,
        'messages': {},
    }
    mock_render.assert_called_once_with(
        application_hub_view_get_request, 'adg/lms/applications/hub.html', context=expected_context
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'are_omni_courses_complete, are_bu_courses_complete',
    [
        (False, False),
        (True, False),
        (True, True)
    ],
    ids=['written_application_complete', 'omni_courses_complete', 'bu_courses_complete'])
def test_each_step_for_application_completion_application_hub_view(
    are_omni_courses_complete, are_bu_courses_complete, application_hub_view_get_request, mocker
):
    """
    Test get request to application hub for each requirement completion till application submission.
    """
    mocker.patch('openedx.adg.lms.applications.views.get_application_hub_instructions', return_value={})
    mocker.patch('openedx.adg.lms.applications.views.get_course_card_information', return_value=([], False, False))
    mock_render = mocker.patch('openedx.adg.lms.applications.views.render')

    application_hub = ApplicationHubFactory(user=application_hub_view_get_request.user)
    application_hub.submit_written_application_for_current_date()

    application = UserApplicationFactory(user=application_hub_view_get_request.user)
    application.business_line = None

    if are_omni_courses_complete:
        application_hub.set_is_prerequisite_courses_passed()

    if are_bu_courses_complete:
        application_hub.set_is_bu_prerequisite_courses_passed()

    ApplicationHubView.as_view()(application_hub_view_get_request)

    expected_context = {
        'user_application_hub': application_hub_view_get_request.user.application_hub,
        'pre_req_courses': [],
        'business_line_courses': [],
        'is_locked': False,
        'messages': {},
    }
    mock_render.assert_called_once_with(
        application_hub_view_get_request, 'adg/lms/applications/hub.html', context=expected_context
    )


# ------- Contact Information View tests below -------


@pytest.fixture(name='get_request_for_contact_information_view')
def get_request_for_contact_information_view_fixture(request_factory, user):
    """
    Create a get request for the contact_information url.
    """
    request = request_factory.get(reverse('application_contact'))
    request.user = user
    return request


@pytest.fixture(name='post_request_for_contact_information_view')
def post_request_for_contact_information_view_fixture(request_factory, user):
    """
    Create a get request for the contact_information url.
    """
    request = request_factory.post(reverse('application_contact'))
    request.user = user
    return request


@pytest.mark.django_db
def test_get_redirects_without_login_for_contact_information_view():
    """
    Test the case where an unauthenticated user is redirected to login page or not.
    """
    application_contact_url = reverse('application_contact')
    response = Client().get(application_contact_url)
    assert f'/register?next={application_contact_url}' == response.url


@pytest.mark.django_db
def test_post_user_redirects_without_login_for_contact_information_view():
    """
    Test the case where an unauthenticated user is redirected to login page or not.
    """
    application_contact_url = reverse('application_contact')
    response = Client().post(application_contact_url)
    assert f'/register?next={application_contact_url}' == response.url


@pytest.mark.django_db
def test_get_already_submitted_application_to_contact_information_view(get_request_for_contact_information_view):
    """
    Test the case where a user with already submitted application hits the url again.
    """
    request = get_request_for_contact_information_view
    request.user.application_hub.submit_written_application_for_current_date()
    response = ContactInformationView.as_view()(request)
    assert response.get('Location') == reverse('application_hub')


@pytest.mark.django_db
def test_post_already_submitted_application_to_contact_information_view(post_request_for_contact_information_view):
    """
    Test the case where a user with already submitted application hits the url again.
    """
    request = post_request_for_contact_information_view
    request.user.application_hub.submit_written_application_for_current_date()
    response = ContactInformationView.as_view()(request)
    assert response.status_code == HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_get_redirects_without_login_for_education_experience_view():
    """
    Test the case where an unauthenticated user is redirected to register page or not.
    """
    response = Client().get(reverse('application_education_experience'))
    assert reverse('register_user') in response.url


@pytest.mark.django_db
def test_get_redirects_after_login_for_education_experience_view(logged_in_client):
    """
    Tests redirects of education experience view for authenticated users if pre condition does not satisfy.
    """
    response = logged_in_client.get(reverse('application_education_experience'))
    assert reverse('application_hub') in response.url


@pytest.mark.django_db
def test_education_experience_view_without_application_hub(user, logged_in_client):
    """
    Test education experience view if application hub is not created for user
    """
    user.application_hub.delete()
    response = logged_in_client.get(reverse('application_education_experience'))
    assert reverse('application_hub') in response.url


@pytest.mark.django_db
def test_get_education_experience_view(request_factory, user):
    """
    Test education experience view if user is authenticated and precondition is satisfied.
    """
    UserApplicationFactory(user=user)
    request = request_factory.get(reverse('application_education_experience'))
    request.user = user
    response = EducationAndExperienceView.as_view()(request)
    assert response.status_code == HTTP_200_OK


# ------- Application Cover Letter View tests below -------


@pytest.fixture(name='cover_letter_view_get_request')
def cover_letter_view_get_request_fixture(request_factory, user):
    """
    Return a HttpRequest object for cover letter get request
    Args:
        request_factory (RequestFactory): factory to make requests
        user (User): The user that is logged in
    Returns:
        HttpRequest object
    """
    request = request_factory.get(reverse('application_cover_letter'))
    request.user = user
    return request


@pytest.fixture(name='cover_letter_view_post_request')
def cover_letter_view_post_request_fixture(request_factory, user):
    """
    Return a HttpRequest object for cover letter post request
    Args:
        request_factory (RequestFactory): factory to make requests
        user (User): The user that is logged in
    Returns:
        HttpRequest object
    """
    request = request_factory.post(reverse('application_cover_letter'))
    request.user = user
    return request


@pytest.mark.django_db
@pytest.mark.parametrize('is_get_request', [True, False], ids=['get_request', 'post_request'])
def test_redirection_of_a_user_without_login_for_cover_letter_view(is_get_request):
    """
    Test if an unauthenticated user is redirected to login page on sending a get or post request.
    """
    if is_get_request:
        response = Client().get(reverse('application_cover_letter'))
    else:
        response = Client().post(reverse('application_cover_letter'))

    assert COVER_LETTER_REDIRECT_URL in response.url


@pytest.mark.django_db
@pytest.mark.parametrize('is_get_request', [True, False], ids=['get_request', 'post_request'])
def test_response_for_user_with_complete_written_application_cover_letter_view(
    is_get_request, cover_letter_view_get_request, cover_letter_view_post_request
):
    """
    Test that if a user who has already completed written application sends a get request, they are redirected to the
    Application Hub page and if a user sends a post request, http 400 is returned.
    """
    request = cover_letter_view_get_request if is_get_request else cover_letter_view_post_request

    request.user.application_hub.submit_written_application_for_current_date()

    response = CoverLetterView.as_view()(request)

    if is_get_request:
        assert response.get('Location') == reverse('application_hub')
        assert response.status_code == 302
    else:
        assert response.status_code == 400


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.views.render')
@mock.patch('openedx.adg.lms.applications.views.BusinessLine.objects.all')
@mock.patch('openedx.adg.lms.applications.views.UserApplicationCoverLetterForm')
@pytest.mark.parametrize('is_user_application_saved', [True, False], ids=['user_application', 'no_user_application'])
def test_get_with_or_without_user_application_cover_letter_view(
    mock_cover_letter_form, mock_business_lines, mock_render, cover_letter_view_get_request, is_user_application_saved
):
    """
    Test that if a user has not yet saved the user application then the class view sends None and if a user has a saved
    instance of user application then the view sends a form of that instance in context upon get request.
    """
    mock_cover_letter_form.return_value = 'form'
    mock_business_lines.return_value = 'business_lines'

    if is_user_application_saved:
        UserApplicationFactory(user=cover_letter_view_get_request.user)
        form = 'form'
    else:
        form = None

    CoverLetterView.as_view()(cover_letter_view_get_request)

    expected_context = {
        'business_lines': 'business_lines',
        'application_form': form
    }

    mock_render.assert_called_once_with(
        cover_letter_view_get_request, 'adg/lms/applications/cover_letter.html', expected_context
    )


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.applications.views.render')
@mock.patch('openedx.adg.lms.applications.views.BusinessLine.objects.all')
@mock.patch('openedx.adg.lms.applications.views.UserApplicationCoverLetterForm')
def test_post_with_business_line_cover_letter_view(
    mock_cover_letter_form, mock_business_lines, mock_render, cover_letter_view_post_request
):
    # pylint: disable=protected-access
    """
    Test the case when the user has selected no business line
    """
    class MockForm:
        def is_valid(self):
            return False

    form = MockForm()

    mock_cover_letter_form.return_value = form
    mock_business_lines.return_value = 'business_lines'

    _mutable = cover_letter_view_post_request.POST._mutable
    cover_letter_view_post_request.POST._mutable = True
    cover_letter_view_post_request.POST['button_click'] = 'back'
    cover_letter_view_post_request.POST._mutable = _mutable

    CoverLetterView.as_view()(cover_letter_view_post_request)

    expected_context = {
        'business_lines': 'business_lines',
        'application_form': form
    }

    mock_render.assert_called_once_with(
        cover_letter_view_post_request, 'adg/lms/applications/cover_letter.html', expected_context
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    'button, template',
    [('back', 'application_education_experience'), ('submit', 'application_hub')],
    ids=['back', 'submit']
)
def test_post_back_or_submit_written_application_cover_letter_view(button, template, cover_letter_view_post_request):
    # pylint: disable=protected-access
    """
    Test that the user is redirected to experience on clicking back and to application hub on submitting.
    """
    business_line = BusinessLineFactory()

    _mutable = cover_letter_view_post_request.POST._mutable
    cover_letter_view_post_request.POST._mutable = True
    cover_letter_view_post_request.POST['business_line'] = business_line.id
    cover_letter_view_post_request.POST['button_click'] = button
    cover_letter_view_post_request.POST._mutable = _mutable

    response = CoverLetterView.as_view()(cover_letter_view_post_request)

    assert response.get('Location') == reverse(template)
    assert response.status_code == 302


@pytest.mark.django_db
@pytest.mark.parametrize(
    'cover_letter, attribute',
    [
        (None, 'cover_letter'),
        ('cover letter', 'cover_letter'),
        (SimpleUploadedFile('cover_letter.png', b'<svg><rect width="50" height="100"/></svg>'), 'cover_letter_file')
    ],
    ids=['no_cover_letter', 'typed_cover_letter', 'cover_letter_file'])
def test_post_with_no_cover_letter_typed_cover_letter_and_file_cover_letter_view(
    cover_letter, attribute, cover_letter_view_post_request
):
    # pylint: disable=protected-access
    """
    Test that whether the user has neither typed a cover letter nor uploaded a file or typed a cover letter or uploaded
    a file, in each case the information is valid
    """
    _mutable = cover_letter_view_post_request.POST._mutable

    business_line = BusinessLineFactory()
    cover_letter_view_post_request.POST._mutable = True

    if attribute == 'cover_letter':
        cover_letter_view_post_request.POST[attribute] = cover_letter
    else:
        cover_letter_view_post_request.FILES[attribute] = cover_letter

    cover_letter_view_post_request.POST['business_line'] = business_line.id
    cover_letter_view_post_request.POST['button_click'] = 'back'
    cover_letter_view_post_request.POST._mutable = _mutable

    response = CoverLetterView.as_view()(cover_letter_view_post_request)

    assert response.get('Location') == reverse('application_education_experience')
    assert response.status_code == 302
