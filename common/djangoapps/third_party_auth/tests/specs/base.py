"""Base integration test for provider implementations."""

import unittest

import json
import mock

from contextlib import contextmanager
from django import test
from django.contrib import auth
from django.contrib.auth import models as auth_models
from django.contrib.messages.storage import fallback
from django.contrib.sessions.backends import cache
from django.core.urlresolvers import reverse
from django.test import utils as django_utils
from django.conf import settings as django_settings
from social import actions, exceptions
from social.apps.django_app import utils as social_utils
from social.apps.django_app import views as social_views

from lms.djangoapps.commerce.tests import TEST_API_URL, TEST_API_SIGNING_KEY
from student import models as student_models
from student import views as student_views
from student.tests.factories import UserFactory
from student_account.views import account_settings_context

from third_party_auth import middleware, pipeline
from third_party_auth import settings as auth_settings
from third_party_auth.tests import testutil


class IntegrationTestMixin(object):
    """
    Mixin base class for third_party_auth integration tests.
    This class is newer and simpler than the 'IntegrationTest' alternative below, but it is
    currently less comprehensive. Some providers are tested with this, others with
    IntegrationTest.
    """
    # Provider information:
    PROVIDER_NAME = "override"
    PROVIDER_BACKEND = "override"
    PROVIDER_ID = "override"
    # Information about the user expected from the provider:
    USER_EMAIL = "override"
    USER_NAME = "override"
    USER_USERNAME = "override"

    def setUp(self):
        super(IntegrationTestMixin, self).setUp()
        self.login_page_url = reverse('signin_user')
        self.register_page_url = reverse('register_user')
        patcher = testutil.patch_mako_templates()
        patcher.start()
        self.addCleanup(patcher.stop)
        # Override this method in a subclass and enable at least one provider.

    def test_register(self, data_sharing_consent=False):
        # The user goes to the register page, and sees a button to register with the provider:
        provider_register_url = self._check_register_page()
        # The user clicks on the Dummy button:
        try_login_response = self.client.get(provider_register_url)
        # The user should be redirected to the provider's login page:
        self.assertEqual(try_login_response.status_code, 302)
        provider_response = self.do_provider_login(try_login_response['Location'])
        # We should be redirected to the register screen since this account is not linked to an edX account:
        self.assertEqual(provider_response.status_code, 302)
        self.assertEqual(provider_response['Location'], self.url_prefix + self.register_page_url)
        register_response = self.client.get(self.register_page_url)
        tpa_context = register_response.context["data"]["third_party_auth"]
        self.assertEqual(tpa_context["errorMessage"], None)
        # Check that the "You've successfully signed into [PROVIDER_NAME]" message is shown.
        self.assertEqual(tpa_context["currentProvider"], self.PROVIDER_NAME)
        # Check that the data (e.g. email) from the provider is displayed in the form:
        form_data = register_response.context['data']['registration_form_desc']
        form_fields = {field['name']: field for field in form_data['fields']}
        self.assertEqual(form_fields['email']['defaultValue'], self.USER_EMAIL)
        self.assertEqual(form_fields['name']['defaultValue'], self.USER_NAME)
        self.assertEqual(form_fields['username']['defaultValue'], self.USER_USERNAME)
        registration_values = {
            'email': 'email-edited@tpa-test.none',
            'name': 'My Customized Name',
            'username': 'new_username',
            'honor_code': True,
        }
        if data_sharing_consent:
            registration_values.update({'data_sharing_consent': True})
        # Now complete the form:
        ajax_register_response = self.client.post(
            reverse('user_api_registration'),
            registration_values
        )
        self.assertEqual(ajax_register_response.status_code, 200)
        # Then the AJAX will finish the third party auth:
        continue_response = self.client.get(tpa_context["finishAuthUrl"])
        # And we should be redirected to the dashboard:
        self.assertEqual(continue_response.status_code, 302)
        self.assertEqual(continue_response['Location'], self.url_prefix + reverse('dashboard'))

        # Now check that we can login again, whether or not we have yet verified the account:
        self.client.logout()
        self._test_return_login(user_is_activated=False)

        self.client.logout()
        self.verify_user_email('email-edited@tpa-test.none')
        self._test_return_login(user_is_activated=True)

    def test_login(self):
        self.user = UserFactory.create()  # pylint: disable=attribute-defined-outside-init
        # The user goes to the login page, and sees a button to login with this provider:
        provider_login_url = self._check_login_page()
        # The user clicks on the provider's button:
        try_login_response = self.client.get(provider_login_url)
        # The user should be redirected to the provider's login page:
        self.assertEqual(try_login_response.status_code, 302)
        complete_response = self.do_provider_login(try_login_response['Location'])
        # We should be redirected to the login screen since this account is not linked to an edX account:
        self.assertEqual(complete_response.status_code, 302)
        self.assertEqual(complete_response['Location'], self.url_prefix + self.login_page_url)
        login_response = self.client.get(self.login_page_url)
        tpa_context = login_response.context["data"]["third_party_auth"]
        self.assertEqual(tpa_context["errorMessage"], None)
        # Check that the "You've successfully signed into [PROVIDER_NAME]" message is shown.
        self.assertEqual(tpa_context["currentProvider"], self.PROVIDER_NAME)
        # Now the user enters their username and password.
        # The AJAX on the page will log them in:
        ajax_login_response = self.client.post(
            reverse('user_api_login_session'),
            {'email': self.user.email, 'password': 'test'}
        )
        self.assertEqual(ajax_login_response.status_code, 200)
        # Then the AJAX will finish the third party auth:
        continue_response = self.client.get(tpa_context["finishAuthUrl"])
        # And we should be redirected to the dashboard:
        self.assertEqual(continue_response.status_code, 302)
        self.assertEqual(continue_response['Location'], self.url_prefix + reverse('dashboard'))

        # Now check that we can login again:
        self.client.logout()
        self._test_return_login()

    def do_provider_login(self, provider_redirect_url):
        """
        mock logging in to the provider
        Should end with loading self.complete_url, which should be returned
        """
        raise NotImplementedError

    def _test_return_login(self, user_is_activated=True):
        """ Test logging in to an account that is already linked. """
        # Make sure we're not logged in:
        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dashboard_response.status_code, 302)
        # The user goes to the login page, and sees a button to login with this provider:
        provider_login_url = self._check_login_page()
        # The user clicks on the provider's login button:
        try_login_response = self.client.get(provider_login_url)
        # The user should be redirected to the provider:
        self.assertEqual(try_login_response.status_code, 302)
        login_response = self.do_provider_login(try_login_response['Location'])
        # There will be one weird redirect required to set the login cookie:
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response['Location'], self.url_prefix + self.complete_url)
        # And then we should be redirected to the dashboard:
        login_response = self.client.get(login_response['Location'])
        self.assertEqual(login_response.status_code, 302)
        if user_is_activated:
            url_expected = reverse('dashboard')
        else:
            url_expected = reverse('third_party_inactive_redirect') + '?next=' + reverse('dashboard')
        self.assertEqual(login_response['Location'], self.url_prefix + url_expected)
        # Now we are logged in:
        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)

    def _check_login_page(self):
        """
        Load the login form and check that it contains a button for the provider.
        Return the URL for logging into that provider.
        """
        return self._check_login_or_register_page(self.login_page_url, "loginUrl")

    def _check_register_page(self):
        """
        Load the registration form and check that it contains a button for the provider.
        Return the URL for registering with that provider.
        """
        return self._check_login_or_register_page(self.register_page_url, "registerUrl")

    def _check_login_or_register_page(self, url, url_to_return):
        """ Shared logic for _check_login_page() and _check_register_page() """
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.PROVIDER_NAME, response.content)
        context_data = response.context['data']['third_party_auth']
        provider_urls = {provider['id']: provider[url_to_return] for provider in context_data['providers']}
        self.assertIn(self.PROVIDER_ID, provider_urls)
        return provider_urls[self.PROVIDER_ID]

    @property
    def complete_url(self):
        """ Get the auth completion URL for this provider """
        return reverse('social:complete', kwargs={'backend': self.PROVIDER_BACKEND})


@unittest.skipUnless(
    testutil.AUTH_FEATURES_KEY in django_settings.FEATURES, testutil.AUTH_FEATURES_KEY + ' not in settings.FEATURES')
@django_utils.override_settings()  # For settings reversion on a method-by-method basis.
class IntegrationTest(testutil.TestCase, test.TestCase):
    """Abstract base class for provider integration tests."""

    # Override setUp and set this:
    provider = None

    # Methods you must override in your children.

    def get_response_data(self):
        """Gets a dict of response data of the form given by the provider.

        To determine what the provider returns, drop into a debugger in your
        provider's do_auth implementation. Providers may merge different kinds
        of data (for example, data about the user and data about the user's
        credentials).
        """
        raise NotImplementedError

    def get_username(self):
        """Gets username based on response data from a provider.

        Each provider has different logic for username generation. Sadly,
        this is not extracted into its own method in python-social-auth, so we
        must provide a getter ourselves.

        Note that this is the *initial* value the framework will attempt to use.
        If it collides, the pipeline will generate a new username. We extract
        it here so we can force collisions in a polymorphic way.
        """
        raise NotImplementedError

    # Asserts you can optionally override and make more specific.

    def assert_redirect_to_provider_looks_correct(self, response):
        """Asserts the redirect to the provider's site looks correct.

        When we hit /auth/login/<provider>, we should be redirected to the
        provider's site. Here we check that we're redirected, but we don't know
        enough about the provider to check what we're redirected to. Child test
        implementations may optionally strengthen this assertion with, for
        example, more details about the format of the Location header.
        """
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.has_header('Location'))

    def assert_register_response_in_pipeline_looks_correct(self, response, pipeline_kwargs):
        """Performs spot checks of the rendered register.html page.

        When we display the new account registration form after the user signs
        in with a third party, we prepopulate the form with values sent back
        from the provider. The exact set of values varies on a provider-by-
        provider basis and is generated by
        provider.BaseProvider.get_register_form_data. We provide some stock
        assertions based on the provider's implementation; if you want more
        assertions in your test, override this method.
        """
        self.assertEqual(200, response.status_code)
        # Check that the correct provider was selected.
        self.assertIn('successfully signed in with <strong>%s</strong>' % self.provider.name, response.content)
        # Expect that each truthy value we've prepopulated the register form
        # with is actually present.
        for prepopulated_form_value in self.provider.get_register_form_data(pipeline_kwargs).values():
            if prepopulated_form_value:
                self.assertIn(prepopulated_form_value, response.content)

    # Implementation details and actual tests past this point -- no more
    # configuration needed.

    def setUp(self):
        super(IntegrationTest, self).setUp()
        self.request_factory = test.RequestFactory()

    @property
    def backend_name(self):
        """ Shortcut for the backend name """
        return self.provider.backend_name

    # pylint: disable=invalid-name
    def assert_account_settings_context_looks_correct(self, context, _user, duplicate=False, linked=None):
        """Asserts the user's account settings page context is in the expected state.

        If duplicate is True, we expect context['duplicate_provider'] to contain
        the duplicate provider backend name. If linked is passed, we conditionally
        check that the provider is included in context['auth']['providers'] and
        its connected state is correct.
        """
        if duplicate:
            self.assertEqual(context['duplicate_provider'], self.provider.backend_name)
        else:
            self.assertIsNone(context['duplicate_provider'])

        if linked is not None:
            expected_provider = [
                provider for provider in context['auth']['providers'] if provider['name'] == self.provider.name
            ][0]
            self.assertIsNotNone(expected_provider)
            self.assertEqual(expected_provider['connected'], linked)

    def assert_exception_redirect_looks_correct(self, expected_uri, auth_entry=None):
        """Tests middleware conditional redirection.

        middleware.ExceptionMiddleware makes sure the user ends up in the right
        place when they cancel authentication via the provider's UX.
        """
        exception_middleware = middleware.ExceptionMiddleware()
        request, _ = self.get_request_and_strategy(auth_entry=auth_entry)
        response = exception_middleware.process_exception(
            request, exceptions.AuthCanceled(request.backend))
        location = response.get('Location')

        self.assertEqual(302, response.status_code)
        self.assertIn('canceled', location)
        self.assertIn(self.backend_name, location)
        self.assertTrue(location.startswith(expected_uri + '?'))

    def assert_first_party_auth_trumps_third_party_auth(self, email=None, password=None, success=None):
        """Asserts first party auth was used in place of third party auth.

        Args:
            email: string. The user's email. If not None, will be set on POST.
            password: string. The user's password. If not None, will be set on
                POST.
            success: None or bool. Whether we expect auth to be successful. Set
                to None to indicate we expect the request to be invalid (meaning
                one of username or password will be missing).
        """
        _, strategy = self.get_request_and_strategy(
            auth_entry=pipeline.AUTH_ENTRY_LOGIN, redirect_uri='social:complete')
        strategy.request.backend.auth_complete = mock.MagicMock(return_value=self.fake_auth_complete(strategy))
        self.create_user_models_for_existing_account(
            strategy, email, password, self.get_username(), skip_social_auth=True)

        strategy.request.POST = dict(strategy.request.POST)

        if email:
            strategy.request.POST['email'] = email
        if password:
            strategy.request.POST['password'] = 'bad_' + password if success is False else password

        self.assert_pipeline_running(strategy.request)
        payload = json.loads(student_views.login_user(strategy.request).content)

        if success is None:
            # Request malformed -- just one of email/password given.
            self.assertFalse(payload.get('success'))
            self.assertIn('There was an error receiving your login information', payload.get('value'))
        elif success:
            # Request well-formed and credentials good.
            self.assertTrue(payload.get('success'))
        else:
            # Request well-formed but credentials bad.
            self.assertFalse(payload.get('success'))
            self.assertIn('incorrect', payload.get('value'))

    def assert_json_failure_response_is_inactive_account(self, response):
        """Asserts failure on /login for inactive account looks right."""
        self.assertEqual(200, response.status_code)  # Yes, it's a 200 even though it's a failure.
        payload = json.loads(response.content)
        self.assertFalse(payload.get('success'))
        self.assertIn('Before you sign in, you need to activate your account', payload.get('value'))

    def assert_json_failure_response_is_missing_social_auth(self, response):
        """Asserts failure on /login for missing social auth looks right."""
        self.assertEqual(403, response.status_code)
        self.assertIn(
            "successfully logged into your %s account, but this account isn't linked" % self.provider.name,
            response.content
        )

    def assert_json_failure_response_is_username_collision(self, response):
        """Asserts the json response indicates a username collision."""
        self.assertEqual(400, response.status_code)
        payload = json.loads(response.content)
        self.assertFalse(payload.get('success'))
        self.assertIn('belongs to an existing account', payload.get('value'))

    def assert_json_success_response_looks_correct(self, response):
        """Asserts the json response indicates success and redirection."""
        self.assertEqual(200, response.status_code)
        payload = json.loads(response.content)
        self.assertTrue(payload.get('success'))
        self.assertEqual(pipeline.get_complete_url(self.provider.backend_name), payload.get('redirect_url'))

    def assert_login_response_before_pipeline_looks_correct(self, response):
        """Asserts a GET of /login not in the pipeline looks correct."""
        self.assertEqual(200, response.status_code)
        # The combined login/registration page dynamically generates the login button,
        # but we can still check that the provider name is passed in the data attribute
        # for the container element.
        self.assertIn(self.provider.name, response.content)

    def assert_login_response_in_pipeline_looks_correct(self, response):
        """Asserts a GET of /login in the pipeline looks correct."""
        self.assertEqual(200, response.status_code)

    def assert_password_overridden_by_pipeline(self, username, password):
        """Verifies that the given password is not correct.

        The pipeline overrides POST['password'], if any, with random data.
        """
        self.assertIsNone(auth.authenticate(password=password, username=username))

    def assert_pipeline_running(self, request):
        """Makes sure the given request is running an auth pipeline."""
        self.assertTrue(pipeline.running(request))

    def assert_redirect_to_dashboard_looks_correct(self, response):
        """Asserts a response would redirect to /dashboard."""
        self.assertEqual(302, response.status_code)
        # pylint: disable=protected-access
        self.assertEqual(auth_settings._SOCIAL_AUTH_LOGIN_REDIRECT_URL, response.get('Location'))

    def assert_redirect_to_login_looks_correct(self, response):
        """Asserts a response would redirect to /login."""
        self.assertEqual(302, response.status_code)
        self.assertEqual('/login', response.get('Location'))

    def assert_redirect_to_register_looks_correct(self, response):
        """Asserts a response would redirect to /register."""
        self.assertEqual(302, response.status_code)
        self.assertEqual('/register', response.get('Location'))

    def assert_register_response_before_pipeline_looks_correct(self, response):
        """Asserts a GET of /register not in the pipeline looks correct."""
        self.assertEqual(200, response.status_code)
        # The combined login/registration page dynamically generates the register button,
        # but we can still check that the provider name is passed in the data attribute
        # for the container element.
        self.assertIn(self.provider.name, response.content)

    def assert_social_auth_does_not_exist_for_user(self, user, strategy):
        """Asserts a user does not have an auth with the expected provider."""
        social_auths = strategy.storage.user.get_social_auth_for_user(
            user, provider=self.provider.backend_name)
        self.assertEqual(0, len(social_auths))

    def assert_social_auth_exists_for_user(self, user, strategy):
        """Asserts a user has a social auth with the expected provider."""
        social_auths = strategy.storage.user.get_social_auth_for_user(
            user, provider=self.provider.backend_name)
        self.assertEqual(1, len(social_auths))
        self.assertEqual(self.backend_name, social_auths[0].provider)

    def create_user_models_for_existing_account(self, strategy, email, password, username, skip_social_auth=False):
        """Creates user, profile, registration, and (usually) social auth.

        This synthesizes what happens during /register.
        See student.views.register and student.views._do_create_account.
        """
        response_data = self.get_response_data()
        uid = strategy.request.backend.get_user_id(response_data, response_data)
        user = social_utils.Storage.user.create_user(email=email, password=password, username=username)
        profile = student_models.UserProfile(user=user)
        profile.save()
        registration = student_models.Registration()
        registration.register(user)
        registration.save()

        if not skip_social_auth:
            social_utils.Storage.user.create_social_auth(user, uid, self.provider.backend_name)

        return user

    def fake_auth_complete(self, strategy):
        """Fake implementation of social.backends.BaseAuth.auth_complete.

        Unlike what the docs say, it does not need to return a user instance.
        Sometimes (like when directing users to the /register form) it instead
        returns a response that 302s to /register.
        """
        args = ()
        kwargs = {
            'request': strategy.request,
            'backend': strategy.request.backend,
            'user': None,
            'response': self.get_response_data(),
        }
        return strategy.authenticate(*args, **kwargs)

    def get_registration_post_vars(self, overrides=None):
        """POST vars generated by the registration form."""
        defaults = {
            'username': 'username',
            'name': 'First Last',
            'gender': '',
            'year_of_birth': '',
            'level_of_education': '',
            'goals': '',
            'honor_code': 'true',
            'terms_of_service': 'true',
            'password': 'password',
            'mailing_address': '',
            'email': 'user@email.com',
        }

        if overrides:
            defaults.update(overrides)

        return defaults

    def get_request_and_strategy(self, auth_entry=None, redirect_uri=None):
        """Gets a fully-configured request and strategy.

        These two objects contain circular references, so we create them
        together. The references themselves are a mixture of normal __init__
        stuff and monkey-patching done by python-social-auth. See, for example,
        social.apps.django_apps.utils.strategy().
        """
        request = self.request_factory.get(
            pipeline.get_complete_url(self.backend_name) +
            '?redirect_state=redirect_state_value&code=code_value&state=state_value')
        request.user = auth_models.AnonymousUser()
        request.session = cache.SessionStore()
        request.session[self.backend_name + '_state'] = 'state_value'

        if auth_entry:
            request.session[pipeline.AUTH_ENTRY_KEY] = auth_entry

        strategy = social_utils.load_strategy(request=request)
        request.social_strategy = strategy
        request.backend = social_utils.load_backend(strategy, self.backend_name, redirect_uri)

        return request, strategy

    @contextmanager
    def _patch_edxmako_current_request(self, request):
        """Make ``request`` be the current request for edxmako template rendering."""

        with mock.patch('edxmako.request_context.get_current_request', return_value=request):
            yield

    def get_user_by_email(self, strategy, email):
        """Gets a user by email, using the given strategy."""
        return strategy.storage.user.user_model().objects.get(email=email)

    def assert_logged_in_cookie_redirect(self, response):
        """Verify that the user was redirected in order to set the logged in cookie. """
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response["Location"],
            pipeline.get_complete_url(self.provider.backend_name)
        )
        self.assertEqual(response.cookies[django_settings.EDXMKTG_LOGGED_IN_COOKIE_NAME].value, 'true')
        self.assertIn(django_settings.EDXMKTG_USER_INFO_COOKIE_NAME, response.cookies)

    def set_logged_in_cookies(self, request):
        """Simulate setting the marketing site cookie on the request. """
        request.COOKIES[django_settings.EDXMKTG_LOGGED_IN_COOKIE_NAME] = 'true'
        request.COOKIES[django_settings.EDXMKTG_USER_INFO_COOKIE_NAME] = json.dumps({
            'version': django_settings.EDXMKTG_USER_INFO_COOKIE_VERSION,
        })

    # Actual tests, executed once per child.

    def test_canceling_authentication_redirects_to_login_when_auth_entry_login(self):
        self.assert_exception_redirect_looks_correct('/login', auth_entry=pipeline.AUTH_ENTRY_LOGIN)

    def test_canceling_authentication_redirects_to_register_when_auth_entry_register(self):
        self.assert_exception_redirect_looks_correct('/register', auth_entry=pipeline.AUTH_ENTRY_REGISTER)

    def test_canceling_authentication_redirects_to_account_settings_when_auth_entry_account_settings(self):
        self.assert_exception_redirect_looks_correct(
            '/account/settings', auth_entry=pipeline.AUTH_ENTRY_ACCOUNT_SETTINGS
        )

    def test_canceling_authentication_redirects_to_root_when_auth_entry_not_set(self):
        self.assert_exception_redirect_looks_correct('/')

    def test_full_pipeline_succeeds_for_linking_account(self):
        # First, create, the request and strategy that store pipeline state,
        # configure the backend, and mock out wire traffic.
        request, strategy = self.get_request_and_strategy(
            auth_entry=pipeline.AUTH_ENTRY_LOGIN, redirect_uri='social:complete')
        request.backend.auth_complete = mock.MagicMock(return_value=self.fake_auth_complete(strategy))
        pipeline.analytics.track = mock.MagicMock()
        request.user = self.create_user_models_for_existing_account(
            strategy, 'user@example.com', 'password', self.get_username(), skip_social_auth=True)

        # Instrument the pipeline to get to the dashboard with the full
        # expected state.
        self.client.get(
            pipeline.get_login_url(self.provider.provider_id, pipeline.AUTH_ENTRY_LOGIN))
        actions.do_complete(request.backend, social_views._do_login)  # pylint: disable=protected-access

        student_views.signin_user(strategy.request)
        student_views.login_user(strategy.request)
        actions.do_complete(request.backend, social_views._do_login)  # pylint: disable=protected-access

        # First we expect that we're in the unlinked state, and that there
        # really is no association in the backend.
        self.assert_account_settings_context_looks_correct(account_settings_context(request), request.user, linked=False)
        self.assert_social_auth_does_not_exist_for_user(request.user, strategy)

        # We should be redirected back to the complete page, setting
        # the "logged in" cookie for the marketing site.
        self.assert_logged_in_cookie_redirect(actions.do_complete(
            request.backend, social_views._do_login, request.user, None,  # pylint: disable=protected-access
            redirect_field_name=auth.REDIRECT_FIELD_NAME
        ))

        # Set the cookie and try again
        self.set_logged_in_cookies(request)

        # Fire off the auth pipeline to link.
        self.assert_redirect_to_dashboard_looks_correct(actions.do_complete(
            request.backend, social_views._do_login, request.user, None,  # pylint: disable=protected-access
            redirect_field_name=auth.REDIRECT_FIELD_NAME))

        # Now we expect to be in the linked state, with a backend entry.
        self.assert_social_auth_exists_for_user(request.user, strategy)
        self.assert_account_settings_context_looks_correct(account_settings_context(request), request.user, linked=True)

    def test_full_pipeline_succeeds_for_unlinking_account(self):
        # First, create, the request and strategy that store pipeline state,
        # configure the backend, and mock out wire traffic.
        request, strategy = self.get_request_and_strategy(
            auth_entry=pipeline.AUTH_ENTRY_LOGIN, redirect_uri='social:complete')
        request.backend.auth_complete = mock.MagicMock(return_value=self.fake_auth_complete(strategy))
        user = self.create_user_models_for_existing_account(
            strategy, 'user@example.com', 'password', self.get_username())
        self.assert_social_auth_exists_for_user(user, strategy)

        # We're already logged in, so simulate that the cookie is set correctly
        self.set_logged_in_cookies(request)

        # Instrument the pipeline to get to the dashboard with the full
        # expected state.
        self.client.get(
            pipeline.get_login_url(self.provider.provider_id, pipeline.AUTH_ENTRY_LOGIN))
        actions.do_complete(request.backend, social_views._do_login)  # pylint: disable=protected-access

        with self._patch_edxmako_current_request(strategy.request):
            student_views.signin_user(strategy.request)
            student_views.login_user(strategy.request)
            actions.do_complete(request.backend, social_views._do_login, user=user)  # pylint: disable=protected-access

        # First we expect that we're in the linked state, with a backend entry.
        self.assert_account_settings_context_looks_correct(account_settings_context(request), user, linked=True)
        self.assert_social_auth_exists_for_user(request.user, strategy)

        # Fire off the disconnect pipeline to unlink.
        self.assert_redirect_to_dashboard_looks_correct(actions.do_disconnect(
            request.backend, request.user, None, redirect_field_name=auth.REDIRECT_FIELD_NAME))

        # Now we expect to be in the unlinked state, with no backend entry.
        self.assert_account_settings_context_looks_correct(account_settings_context(request), user, linked=False)
        self.assert_social_auth_does_not_exist_for_user(user, strategy)

    def test_linking_already_associated_account_raises_auth_already_associated(self):
        # This is of a piece with
        # test_already_associated_exception_populates_dashboard_with_error. It
        # verifies the exception gets raised when we expect; the latter test
        # covers exception handling.
        email = 'user@example.com'
        password = 'password'
        username = self.get_username()
        _, strategy = self.get_request_and_strategy(
            auth_entry=pipeline.AUTH_ENTRY_LOGIN, redirect_uri='social:complete')
        backend = strategy.request.backend
        backend.auth_complete = mock.MagicMock(return_value=self.fake_auth_complete(strategy))
        linked_user = self.create_user_models_for_existing_account(strategy, email, password, username)
        unlinked_user = social_utils.Storage.user.create_user(
            email='other_' + email, password=password, username='other_' + username)

        self.assert_social_auth_exists_for_user(linked_user, strategy)
        self.assert_social_auth_does_not_exist_for_user(unlinked_user, strategy)

        with self.assertRaises(exceptions.AuthAlreadyAssociated):
            # pylint: disable=protected-access
            actions.do_complete(backend, social_views._do_login, user=unlinked_user)

    def test_already_associated_exception_populates_dashboard_with_error(self):
        # Instrument the pipeline with an exception. We test that the
        # exception is raised correctly separately, so it's ok that we're
        # raising it artificially here. This makes the linked=True artificial
        # in the final assert because in practice the account would be
        # unlinked, but getting that behavior is cumbersome here and already
        # covered in other tests. Using linked=True does, however, let us test
        # that the duplicate error has no effect on the state of the controls.
        request, strategy = self.get_request_and_strategy(
            auth_entry=pipeline.AUTH_ENTRY_LOGIN, redirect_uri='social:complete')
        strategy.request.backend.auth_complete = mock.MagicMock(return_value=self.fake_auth_complete(strategy))
        user = self.create_user_models_for_existing_account(
            strategy, 'user@example.com', 'password', self.get_username())
        self.assert_social_auth_exists_for_user(user, strategy)

        self.client.get('/login')
        self.client.get(pipeline.get_login_url(self.provider.provider_id, pipeline.AUTH_ENTRY_LOGIN))
        actions.do_complete(request.backend, social_views._do_login)  # pylint: disable=protected-access

        with self._patch_edxmako_current_request(strategy.request):
            student_views.signin_user(strategy.request)
            student_views.login_user(strategy.request)
            actions.do_complete(request.backend, social_views._do_login, user=user)  # pylint: disable=protected-access

        # Monkey-patch storage for messaging; pylint: disable=protected-access
        request._messages = fallback.FallbackStorage(request)
        middleware.ExceptionMiddleware().process_exception(
            request,
            exceptions.AuthAlreadyAssociated(self.provider.backend_name, 'account is already in use.'))

        self.assert_account_settings_context_looks_correct(
            account_settings_context(request), user, duplicate=True, linked=True)

    def test_full_pipeline_succeeds_for_signing_in_to_existing_active_account(self):
        # First, create, the request and strategy that store pipeline state,
        # configure the backend, and mock out wire traffic.
        request, strategy = self.get_request_and_strategy(
            auth_entry=pipeline.AUTH_ENTRY_LOGIN, redirect_uri='social:complete')
        strategy.request.backend.auth_complete = mock.MagicMock(return_value=self.fake_auth_complete(strategy))
        pipeline.analytics.track = mock.MagicMock()
        user = self.create_user_models_for_existing_account(
            strategy, 'user@example.com', 'password', self.get_username())
        self.assert_social_auth_exists_for_user(user, strategy)
        self.assertTrue(user.is_active)

        # Begin! Ensure that the login form contains expected controls before
        # the user starts the pipeline.
        self.assert_login_response_before_pipeline_looks_correct(self.client.get('/login'))

        # The pipeline starts by a user GETting /auth/login/<provider>.
        # Synthesize that request and check that it redirects to the correct
        # provider page.
        self.assert_redirect_to_provider_looks_correct(self.client.get(
            pipeline.get_login_url(self.provider.provider_id, pipeline.AUTH_ENTRY_LOGIN)))

        # Next, the provider makes a request against /auth/complete/<provider>
        # to resume the pipeline.
        # pylint: disable=protected-access
        self.assert_redirect_to_login_looks_correct(actions.do_complete(request.backend, social_views._do_login))

        # At this point we know the pipeline has resumed correctly. Next we
        # fire off the view that displays the login form and posts it via JS.
        with self._patch_edxmako_current_request(strategy.request):
            self.assert_login_response_in_pipeline_looks_correct(student_views.signin_user(strategy.request))

        # Next, we invoke the view that handles the POST, and expect it
        # redirects to /auth/complete. In the browser ajax handlers will
        # redirect the user to the dashboard; we invoke it manually here.
        self.assert_json_success_response_looks_correct(student_views.login_user(strategy.request))

        # We should be redirected back to the complete page, setting
        # the "logged in" cookie for the marketing site.
        self.assert_logged_in_cookie_redirect(actions.do_complete(
            request.backend, social_views._do_login, request.user, None,  # pylint: disable=protected-access
            redirect_field_name=auth.REDIRECT_FIELD_NAME
        ))

        # Set the cookie and try again
        self.set_logged_in_cookies(request)

        self.assert_redirect_to_dashboard_looks_correct(
            actions.do_complete(request.backend, social_views._do_login, user=user))
        self.assert_account_settings_context_looks_correct(account_settings_context(request), user)

    def test_signin_fails_if_account_not_active(self):
        _, strategy = self.get_request_and_strategy(
            auth_entry=pipeline.AUTH_ENTRY_LOGIN, redirect_uri='social:complete')
        strategy.request.backend.auth_complete = mock.MagicMock(return_value=self.fake_auth_complete(strategy))
        user = self.create_user_models_for_existing_account(strategy, 'user@example.com', 'password', self.get_username())

        user.is_active = False
        user.save()

        with self._patch_edxmako_current_request(strategy.request):
            self.assert_json_failure_response_is_inactive_account(student_views.login_user(strategy.request))

    def test_signin_fails_if_no_account_associated(self):
        _, strategy = self.get_request_and_strategy(
            auth_entry=pipeline.AUTH_ENTRY_LOGIN, redirect_uri='social:complete')
        strategy.request.backend.auth_complete = mock.MagicMock(return_value=self.fake_auth_complete(strategy))
        self.create_user_models_for_existing_account(
            strategy, 'user@example.com', 'password', self.get_username(), skip_social_auth=True)

        self.assert_json_failure_response_is_missing_social_auth(student_views.login_user(strategy.request))

    def test_first_party_auth_trumps_third_party_auth_but_is_invalid_when_only_email_in_request(self):
        self.assert_first_party_auth_trumps_third_party_auth(email='user@example.com')

    def test_first_party_auth_trumps_third_party_auth_but_is_invalid_when_only_password_in_request(self):
        self.assert_first_party_auth_trumps_third_party_auth(password='password')

    def test_first_party_auth_trumps_third_party_auth_and_fails_when_credentials_bad(self):
        self.assert_first_party_auth_trumps_third_party_auth(
            email='user@example.com', password='password', success=False)

    def test_first_party_auth_trumps_third_party_auth_and_succeeds_when_credentials_good(self):
        self.assert_first_party_auth_trumps_third_party_auth(
            email='user@example.com', password='password', success=True)

    def test_full_pipeline_succeeds_registering_new_account(self):
        # First, create, the request and strategy that store pipeline state.
        # Mock out wire traffic.
        request, strategy = self.get_request_and_strategy(
            auth_entry=pipeline.AUTH_ENTRY_REGISTER, redirect_uri='social:complete')
        strategy.request.backend.auth_complete = mock.MagicMock(return_value=self.fake_auth_complete(strategy))

        # Begin! Grab the registration page and check the login control on it.
        self.assert_register_response_before_pipeline_looks_correct(self.client.get('/register'))

        # The pipeline starts by a user GETting /auth/login/<provider>.
        # Synthesize that request and check that it redirects to the correct
        # provider page.
        self.assert_redirect_to_provider_looks_correct(self.client.get(
            pipeline.get_login_url(self.provider.provider_id, pipeline.AUTH_ENTRY_LOGIN)))

        # Next, the provider makes a request against /auth/complete/<provider>.
        # pylint: disable=protected-access
        self.assert_redirect_to_register_looks_correct(actions.do_complete(request.backend, social_views._do_login))

        # At this point we know the pipeline has resumed correctly. Next we
        # fire off the view that displays the registration form.
        with self._patch_edxmako_current_request(request):
            self.assert_register_response_in_pipeline_looks_correct(
                student_views.register_user(strategy.request), pipeline.get(request)['kwargs'])

        # Next, we invoke the view that handles the POST. Not all providers
        # supply email. Manually add it as the user would have to; this
        # also serves as a test of overriding provider values. Always provide a
        # password for us to check that we override it properly.
        overridden_password = strategy.request.POST.get('password')
        email = 'new@example.com'

        if not strategy.request.POST.get('email'):
            strategy.request.POST = self.get_registration_post_vars({'email': email})

        # The user must not exist yet...
        with self.assertRaises(auth_models.User.DoesNotExist):
            self.get_user_by_email(strategy, email)

        # ...but when we invoke create_account the existing edX view will make
        # it, but not social auths. The pipeline creates those later.
        with self._patch_edxmako_current_request(strategy.request):
            self.assert_json_success_response_looks_correct(student_views.create_account(strategy.request))
        # We've overridden the user's password, so authenticate() with the old
        # value won't work:
        created_user = self.get_user_by_email(strategy, email)
        self.assert_password_overridden_by_pipeline(overridden_password, created_user.username)

        # At this point the user object exists, but there is no associated
        # social auth.
        self.assert_social_auth_does_not_exist_for_user(created_user, strategy)

        # We should be redirected back to the complete page, setting
        # the "logged in" cookie for the marketing site.
        self.assert_logged_in_cookie_redirect(actions.do_complete(
            request.backend, social_views._do_login, request.user, None,  # pylint: disable=protected-access
            redirect_field_name=auth.REDIRECT_FIELD_NAME
        ))

        # Set the cookie and try again
        self.set_logged_in_cookies(request)
        self.assert_redirect_to_dashboard_looks_correct(
            actions.do_complete(strategy.request.backend, social_views._do_login, user=created_user))
        # Now the user has been redirected to the dashboard. Their third party account should now be linked.
        self.assert_social_auth_exists_for_user(created_user, strategy)
        self.assert_account_settings_context_looks_correct(account_settings_context(request), created_user, linked=True)

    def test_new_account_registration_assigns_distinct_username_on_collision(self):
        original_username = self.get_username()
        request, strategy = self.get_request_and_strategy(
            auth_entry=pipeline.AUTH_ENTRY_REGISTER, redirect_uri='social:complete')

        # Create a colliding username in the backend, then proceed with
        # assignment via pipeline to make sure a distinct username is created.
        strategy.storage.user.create_user(username=self.get_username(), email='user@email.com', password='password')
        backend = strategy.request.backend
        backend.auth_complete = mock.MagicMock(return_value=self.fake_auth_complete(strategy))
        # pylint: disable=protected-access
        self.assert_redirect_to_register_looks_correct(actions.do_complete(backend, social_views._do_login))
        distinct_username = pipeline.get(request)['kwargs']['username']
        self.assertNotEqual(original_username, distinct_username)

    def test_new_account_registration_fails_if_email_exists(self):
        request, strategy = self.get_request_and_strategy(
            auth_entry=pipeline.AUTH_ENTRY_REGISTER, redirect_uri='social:complete')
        backend = strategy.request.backend
        backend.auth_complete = mock.MagicMock(return_value=self.fake_auth_complete(strategy))
        # pylint: disable=protected-access
        self.assert_redirect_to_register_looks_correct(actions.do_complete(backend, social_views._do_login))

        with self._patch_edxmako_current_request(request):
            self.assert_register_response_in_pipeline_looks_correct(
                student_views.register_user(strategy.request), pipeline.get(request)['kwargs'])

        with self._patch_edxmako_current_request(strategy.request):
            strategy.request.POST = self.get_registration_post_vars()
            # Create twice: once successfully, and once causing a collision.
            student_views.create_account(strategy.request)
        self.assert_json_failure_response_is_username_collision(student_views.create_account(strategy.request))

    def test_pipeline_raises_auth_entry_error_if_auth_entry_invalid(self):
        auth_entry = 'invalid'
        self.assertNotIn(auth_entry, pipeline._AUTH_ENTRY_CHOICES)  # pylint: disable=protected-access

        _, strategy = self.get_request_and_strategy(auth_entry=auth_entry, redirect_uri='social:complete')

        with self.assertRaises(pipeline.AuthEntryError):
            strategy.request.backend.auth_complete = mock.MagicMock(return_value=self.fake_auth_complete(strategy))

    def test_pipeline_raises_auth_entry_error_if_auth_entry_missing(self):
        _, strategy = self.get_request_and_strategy(auth_entry=None, redirect_uri='social:complete')

        with self.assertRaises(pipeline.AuthEntryError):
            strategy.request.backend.auth_complete = mock.MagicMock(return_value=self.fake_auth_complete(strategy))


# pylint: disable=test-inherits-tests, abstract-method
@django_utils.override_settings(ECOMMERCE_API_URL=TEST_API_URL, ECOMMERCE_API_SIGNING_KEY=TEST_API_SIGNING_KEY)
class Oauth2IntegrationTest(IntegrationTest):
    """Base test case for integration tests of Oauth2 providers."""

    # Dict of string -> object. Information about the token granted to the
    # user. Override with test values in subclass; None to force a throw.
    TOKEN_RESPONSE_DATA = None

    # Dict of string -> object. Information about the user themself. Override
    # with test values in subclass; None to force a throw.
    USER_RESPONSE_DATA = None

    def get_response_data(self):
        """Gets dict (string -> object) of merged data about the user."""
        response_data = dict(self.TOKEN_RESPONSE_DATA)
        response_data.update(self.USER_RESPONSE_DATA)
        return response_data
