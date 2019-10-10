from contextlib import contextmanager

import mock
from django.core.exceptions import NON_FIELD_ERRORS
from django.core.validators import ValidationError
from lms.djangoapps.onboarding.models import RegistrationType
from lms.djangoapps.philu_overrides.helpers import save_user_partner_network_consent
from lms.djangoapps.philu_overrides.user_api.views import create_account_with_params_custom
from student.cookies import set_logged_in_cookies
from util.json_request import JsonResponse


@contextmanager
def simulate_running_pipeline(pipeline_target, backend, email=None, fullname=None, username=None):
    """Simulate that a pipeline is currently running.

    You can use this context manager to test packages that rely on third party auth.

    This uses `mock.patch` to override some calls in `third_party_auth.pipeline`,
    so you will need to provide the "target" module *as it is imported*
    in the software under test.  For example, if `foo/bar.py` does this:

    >>> from third_party_auth import pipeline

    then you will need to do something like this:

    >>> with simulate_running_pipeline("foo.bar.pipeline", "google-oauth2"):
    >>>    bar.do_something_with_the_pipeline()

    If, on the other hand, `foo/bar.py` had done this:

    >>> import third_party_auth

    then you would use the target "foo.bar.third_party_auth.pipeline" instead.

    Arguments:

        pipeline_target (string): The path to `third_party_auth.pipeline` as it is imported
            in the software under test.

        backend (string): The name of the backend currently running, for example "google-oauth2".
            Note that this is NOT the same as the name of the *provider*.  See the Python
            social auth documentation for the names of the backends.

    Keyword Arguments:
        email (string): If provided, simulate that the current provider has
            included the user's email address (useful for filling in the registration form).

        fullname (string): If provided, simulate that the current provider has
            included the user's full name (useful for filling in the registration form).

        username (string): If provided, simulate that the pipeline has provided
            this suggested username.  This is something that the `third_party_auth`
            app generates itself and should be available by the time the user
            is authenticating with a third-party provider.

    Returns:
        None

    """
    pipeline_data = {
        "backend": backend,
        "kwargs": {
            "details": {},
            'response': {
                'access_token': 'dummy access token'
            }
        }
    }

    if email is not None:
        pipeline_data["kwargs"]["details"]["email"] = email
    if fullname is not None:
        pipeline_data["kwargs"]["details"]["fullname"] = fullname
    if username is not None:
        pipeline_data["kwargs"]["username"] = username

    pipeline_get = mock.patch("{pipeline}.get".format(pipeline=pipeline_target), spec=True)
    pipeline_running = mock.patch("{pipeline}.running".format(pipeline=pipeline_target), spec=True)

    mock_get = pipeline_get.start()
    mock_running = pipeline_running.start()

    mock_get.return_value = pipeline_data
    mock_running.return_value = True

    try:
        yield

    finally:
        pipeline_get.stop()
        pipeline_running.stop()


def mocked_registration_view_post_method(self, request):
    data = request.POST.copy()

    email = data.get('email')
    username = data.get('username')
    is_alquity_user = data.get('is_alquity_user') or False

    # Backwards compatibility: the student view expects both
    # terms of service and honor code values.  Since we're combining
    # these into a single checkbox, the only value we may get
    # from the new view is "honor_code".
    # Longer term, we will need to make this more flexible to support
    # open source installations that may have separate checkboxes
    # for TOS, privacy policy, etc.
    if data.get("honor_code") and "terms_of_service" not in data:
        data["terms_of_service"] = data["honor_code"]

    try:
        user = create_account_with_params_custom(request, data, is_alquity_user)
        self.save_user_utm_info(user)
        save_user_partner_network_consent(user, data['partners_opt_in'])
    except ValidationError as err:
        # Should only get non-field errors from this function
        assert NON_FIELD_ERRORS not in err.message_dict
        # Only return first error for each field
        errors = {
            field: [{"user_message": error} for error in error_list]
            for field, error_list in err.message_dict.items()
        }
        return JsonResponse(errors, status=400)

    RegistrationType.objects.create(choice=1, user=request.user)
    response = JsonResponse({"success": True})
    set_logged_in_cookies(request, response, user)
    return response
