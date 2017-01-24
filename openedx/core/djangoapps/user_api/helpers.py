"""
Helper functions for the account/profile Python APIs.
This is NOT part of the public API.
"""
from collections import defaultdict
from functools import wraps
import logging
import json

from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponseBadRequest
from django.utils.encoding import force_text
from django.utils.functional import Promise

LOGGER = logging.getLogger(__name__)


def intercept_errors(api_error, ignore_errors=None):
    """
    Function decorator that intercepts exceptions
    and translates them into API-specific errors (usually an "internal" error).

    This allows callers to gracefully handle unexpected errors from the API.

    This method will also log all errors and function arguments to make
    it easier to track down unexpected errors.

    Arguments:
        api_error (Exception): The exception to raise if an unexpected error is encountered.

    Keyword Arguments:
        ignore_errors (iterable): List of errors to ignore.  By default, intercept every error.

    Returns:
        function

    """
    def _decorator(func):
        """
        Function decorator that intercepts exceptions and translates them into API-specific errors.
        """
        @wraps(func)
        def _wrapped(*args, **kwargs):
            """
            Wrapper that evaluates a function, intercepting exceptions and translating them into
            API-specific errors.
            """
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                # Raise and log the original exception if it's in our list of "ignored" errors
                for ignored in ignore_errors or []:
                    if isinstance(ex, ignored):
                        msg = (
                            u"A handled error occurred when calling '{func_name}' "
                            u"with arguments '{args}' and keyword arguments '{kwargs}': "
                            u"{exception}"
                        ).format(
                            func_name=func.func_name,
                            args=args,
                            kwargs=kwargs,
                            exception=ex.developer_message if hasattr(ex, 'developer_message') else repr(ex)
                        )
                        LOGGER.warning(msg)
                        raise

                # Otherwise, log the error and raise the API-specific error
                msg = (
                    u"An unexpected error occurred when calling '{func_name}' "
                    u"with arguments '{args}' and keyword arguments '{kwargs}': "
                    u"{exception}"
                ).format(
                    func_name=func.func_name,
                    args=args,
                    kwargs=kwargs,
                    exception=ex.developer_message if hasattr(ex, 'developer_message') else repr(ex)
                )
                LOGGER.exception(msg)
                raise api_error(msg)
        return _wrapped
    return _decorator


def require_post_params(required_params):
    """
    View decorator that ensures the required POST params are
    present.  If not, returns an HTTP response with status 400.

    Args:
        required_params (list): The required parameter keys.

    Returns:
        HttpResponse

    """
    def _decorator(func):  # pylint: disable=missing-docstring
        @wraps(func)
        def _wrapped(*args, **_kwargs):  # pylint: disable=missing-docstring
            request = args[0]
            missing_params = set(required_params) - set(request.POST.keys())
            if len(missing_params) > 0:
                msg = u"Missing POST parameters: {missing}".format(
                    missing=", ".join(missing_params)
                )
                return HttpResponseBadRequest(msg)
            else:
                return func(request)
        return _wrapped
    return _decorator


class InvalidFieldError(Exception):
    """The provided field definition is not valid. """


class FormDescription(object):
    """Generate a JSON representation of a form. """

    ALLOWED_TYPES = ["text", "email", "select", "textarea", "checkbox", "password"]

    ALLOWED_RESTRICTIONS = {
        "text": ["min_length", "max_length"],
        "password": ["min_length", "max_length"],
        "email": ["min_length", "max_length"],
    }

    FIELD_TYPE_MAP = {
        forms.CharField: "text",
        forms.PasswordInput: "password",
        forms.ChoiceField: "select",
        forms.TypedChoiceField: "select",
        forms.Textarea: "textarea",
        forms.BooleanField: "checkbox",
        forms.EmailField: "email",
    }

    OVERRIDE_FIELD_PROPERTIES = [
        "label", "type", "defaultValue", "placeholder",
        "instructions", "required", "restrictions",
        "options", "supplementalLink", "supplementalText"
    ]

    def __init__(self, method, submit_url):
        """Configure how the form should be submitted.

        Args:
            method (unicode): The HTTP method used to submit the form.
            submit_url (unicode): The URL where the form should be submitted.

        """
        self.method = method
        self.submit_url = submit_url
        self.fields = []
        self._field_overrides = defaultdict(dict)

    def add_field(
            self, name, label=u"", field_type=u"text", default=u"",
            placeholder=u"", instructions=u"", required=True, restrictions=None,
            options=None, include_default_option=False, error_messages=None,
            supplementalLink=u"", supplementalText=u""
    ):
        """Add a field to the form description.

        Args:
            name (unicode): The name of the field, which is the key for the value
                to send back to the server.

        Keyword Arguments:
            label (unicode): The label for the field (e.g. "E-mail" or "Username")

            field_type (unicode): The type of the field.  See `ALLOWED_TYPES` for
                acceptable values.

            default (unicode): The default value for the field.

            placeholder (unicode): Placeholder text in the field
                (e.g. "user@example.com" for an email field)

            instructions (unicode): Short instructions for using the field
                (e.g. "This is the email address you used when you registered.")

            required (boolean): Whether the field is required or optional.

            restrictions (dict): Validation restrictions for the field.
                See `ALLOWED_RESTRICTIONS` for acceptable values.

            options (list): For "select" fields, a list of tuples
                (value, display_name) representing the options available to
                the user.  `value` is the value of the field to send to the server,
                and `display_name` is the name to display to the user.
                If the field type is "select", you *must* provide this kwarg.

            include_default_option (boolean): If True, include a "default" empty option
                at the beginning of the options list.

            error_messages (dict): Custom validation error messages.
                Currently, the only supported key is "required" indicating
                that the messages should be displayed if the user does
                not provide a value for a required field.

            supplementalLink (unicode): A qualified URL to provide supplemental information
                for the form field. An example may be a link to documentation for creating
                strong passwords.

            supplementalText (unicode): The visible text for the supplemental link above.

        Raises:
            InvalidFieldError

        """
        if field_type not in self.ALLOWED_TYPES:
            msg = u"Field type '{field_type}' is not a valid type.  Allowed types are: {allowed}.".format(
                field_type=field_type,
                allowed=", ".join(self.ALLOWED_TYPES)
            )
            raise InvalidFieldError(msg)

        field_dict = {
            "name": name,
            "label": label,
            "type": field_type,
            "defaultValue": default,
            "placeholder": placeholder,
            "instructions": instructions,
            "required": required,
            "restrictions": {},
            "errorMessages": {},
            "supplementalLink": supplementalLink,
            "supplementalText": supplementalText
        }

        if field_type == "select":
            if options is not None:
                field_dict["options"] = []

                # Include an empty "default" option at the beginning of the list
                if include_default_option:
                    field_dict["options"].append({
                        "value": "",
                        "name": "--",
                        "default": True
                    })

                field_dict["options"].extend([
                    {"value": option_value, "name": option_name}
                    for option_value, option_name in options
                ])
            else:
                raise InvalidFieldError("You must provide options for a select field.")

        if restrictions is not None:
            allowed_restrictions = self.ALLOWED_RESTRICTIONS.get(field_type, [])
            for key, val in restrictions.iteritems():
                if key in allowed_restrictions:
                    field_dict["restrictions"][key] = val
                else:
                    msg = "Restriction '{restriction}' is not allowed for field type '{field_type}'".format(
                        restriction=key,
                        field_type=field_type
                    )
                    raise InvalidFieldError(msg)

        if error_messages is not None:
            field_dict["errorMessages"] = error_messages

        # If there are overrides for this field, apply them now.
        # Any field property can be overwritten (for example, the default value or placeholder)
        field_dict.update(self._field_overrides.get(name, {}))

        self.fields.append(field_dict)

    def to_json(self):
        """Create a JSON representation of the form description.

        Here's an example of the output:
        {
            "method": "post",
            "submit_url": "/submit",
            "fields": [
                {
                    "name": "cheese_or_wine",
                    "label": "Cheese or Wine?",
                    "defaultValue": "cheese",
                    "type": "select",
                    "required": True,
                    "placeholder": "",
                    "instructions": "",
                    "options": [
                        {"value": "cheese", "name": "Cheese"},
                        {"value": "wine", "name": "Wine"}
                    ]
                    "restrictions": {},
                    "errorMessages": {},
                },
                {
                    "name": "comments",
                    "label": "comments",
                    "defaultValue": "",
                    "type": "text",
                    "required": False,
                    "placeholder": "Any comments?",
                    "instructions": "Please enter additional comments here."
                    "restrictions": {
                        "max_length": 200
                    }
                    "errorMessages": {},
                },
                ...
            ]
        }

        If the field is NOT a "select" type, then the "options"
        key will be omitted.

        Returns:
            unicode
        """
        return json.dumps({
            "method": self.method,
            "submit_url": self.submit_url,
            "fields": self.fields
        }, cls=LocalizedJSONEncoder)

    def override_field_properties(self, field_name, **kwargs):
        """Override properties of a field.

        The overridden values take precedence over the values provided
        to `add_field()`.

        Field properties not in `OVERRIDE_FIELD_PROPERTIES` will be ignored.

        Arguments:
            field_name (str): The name of the field to override.

        Keyword Args:
            Same as to `add_field()`.

        """
        # Transform kwarg "field_type" to "type" (a reserved Python keyword)
        if "field_type" in kwargs:
            kwargs["type"] = kwargs["field_type"]

        # Transform kwarg "default" to "defaultValue", since "default"
        # is a reserved word in JavaScript
        if "default" in kwargs:
            kwargs["defaultValue"] = kwargs["default"]

        self._field_overrides[field_name].update({
            property_name: property_value
            for property_name, property_value in kwargs.iteritems()
            if property_name in self.OVERRIDE_FIELD_PROPERTIES
        })


class LocalizedJSONEncoder(DjangoJSONEncoder):
    """
    JSON handler that evaluates ugettext_lazy promises.
    """
    # pylint: disable=method-hidden
    def default(self, obj):
        """
        Forces evaluation of ugettext_lazy promises.
        """
        if isinstance(obj, Promise):
            return force_text(obj)
        super(LocalizedJSONEncoder, self).default(obj)


def shim_student_view(view_func, check_logged_in=False):
    """Create a "shim" view for a view function from the student Django app.

    Specifically, we need to:
    * Strip out enrollment params, since the client for the new registration/login
        page will communicate with the enrollment API to update enrollments.

    * Return responses with HTTP status codes indicating success/failure
        (instead of always using status 200, but setting "success" to False in
        the JSON-serialized content of the response)

    * Use status code 403 to indicate a login failure.

    The shim will preserve any cookies set by the view.

    Arguments:
        view_func (function): The view function from the student Django app.

    Keyword Args:
        check_logged_in (boolean): If true, check whether the user successfully
            authenticated and if not set the status to 403.

    Returns:
        function

    """
    @wraps(view_func)
    def _inner(request):  # pylint: disable=missing-docstring
        # Ensure that the POST querydict is mutable
        request.POST = request.POST.copy()

        # The login and registration handlers in student view try to change
        # the user's enrollment status if these parameters are present.
        # Since we want the JavaScript client to communicate directly with
        # the enrollment API, we want to prevent the student views from
        # updating enrollments.
        if "enrollment_action" in request.POST:
            del request.POST["enrollment_action"]
        if "course_id" in request.POST:
            del request.POST["course_id"]

        # Include the course ID if it's specified in the analytics info
        # so it can be included in analytics events.
        if "analytics" in request.POST:
            try:
                analytics = json.loads(request.POST["analytics"])
                if "enroll_course_id" in analytics:
                    request.POST["course_id"] = analytics.get("enroll_course_id")
            except (ValueError, TypeError):
                LOGGER.error(
                    u"Could not parse analytics object sent to user API: {analytics}".format(
                        analytics=analytics
                    )
                )

        # Call the original view to generate a response.
        # We can safely modify the status code or content
        # of the response, but to be safe we won't mess
        # with the headers.
        response = view_func(request)

        # Most responses from this view are JSON-encoded
        # dictionaries with keys "success", "value", and
        # (sometimes) "redirect_url".
        #
        # We want to communicate some of this information
        # using HTTP status codes instead.
        #
        # We ignore the "redirect_url" parameter, because we don't need it:
        # 1) It's used to redirect on change enrollment, which
        # our client will handle directly
        # (that's why we strip out the enrollment params from the request)
        # 2) It's used by third party auth when a user has already successfully
        # authenticated and we're not sending login credentials.  However,
        # this case is never encountered in practice: on the old login page,
        # the login form would be submitted directly, so third party auth
        # would always be "trumped" by first party auth.  If a user has
        # successfully authenticated with us, we redirect them to the dashboard
        # regardless of how they authenticated; and if a user is completing
        # the third party auth pipeline, we redirect them from the pipeline
        # completion end-point directly.
        try:
            response_dict = json.loads(response.content)
            msg = response_dict.get("value", u"")
            success = response_dict.get("success")
        except (ValueError, TypeError):
            msg = response.content
            success = True

        # If the user is not authenticated when we expect them to be
        # send the appropriate status code.
        # We check whether the user attribute is set to make
        # it easier to test this without necessarily running
        # the request through authentication middleware.
        is_authenticated = (
            getattr(request, 'user', None) is not None
            and request.user.is_authenticated()
        )
        if check_logged_in and not is_authenticated:
            # If we get a 403 status code from the student view
            # this means we've successfully authenticated with a
            # third party provider, but we don't have a linked
            # EdX account.  Send a helpful error code so the client
            # knows this occurred.
            if response.status_code == 403:
                response.content = "third-party-auth"

            # Otherwise, it's a general authentication failure.
            # Ensure that the status code is a 403 and pass
            # along the message from the view.
            else:
                response.status_code = 403
                response.content = msg

        # If an error condition occurs, send a status 400
        elif response.status_code != 200 or not success:
            # The student views tend to send status 200 even when an error occurs
            # If the JSON-serialized content has a value "success" set to False,
            # then we know an error occurred.
            if response.status_code == 200:
                response.status_code = 400
            response.content = msg

        # If the response is successful, then return the content
        # of the response directly rather than including it
        # in a JSON-serialized dictionary.
        else:
            response.content = msg

        # Return the response, preserving the original headers.
        # This is really important, since the student views set cookies
        # that are used elsewhere in the system (such as the marketing site).
        return response

    return _inner
