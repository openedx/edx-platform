"""
Helper functions for the account/profile Python APIs.
This is NOT part of the public API.
"""
from functools import wraps
import logging
import json
from django.http import HttpResponseBadRequest


LOGGER = logging.getLogger(__name__)


def intercept_errors(api_error, ignore_errors=[]):
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
        @wraps(func)
        def _wrapped(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                # Raise the original exception if it's in our list of "ignored" errors
                for ignored in ignore_errors:
                    if isinstance(ex, ignored):
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
                    exception=repr(ex)
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
    def _decorator(func):
        @wraps(func)
        def _wrapped(*args, **kwargs):
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

    ALLOWED_TYPES = ["text", "select", "textarea"]

    ALLOWED_RESTRICTIONS = {
        "text": ["min_length", "max_length"],
    }

    def __init__(self, method, submit_url):
        """Configure how the form should be submitted.

        Args:
            method (unicode): The HTTP method used to submit the form.
            submit_url (unicode): The URL where the form should be submitted.

        """
        self.method = method
        self.submit_url = submit_url
        self.fields = []

    def add_field(
        self, name, label=u"", field_type=u"text", default=u"",
        placeholder=u"", instructions=u"", required=True, restrictions=None,
        options=None
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
            "label": label,
            "name": name,
            "type": field_type,
            "default": default,
            "placeholder": placeholder,
            "instructions": instructions,
            "required": required,
            "restrictions": {}
        }

        if field_type == "select":
            if options is not None:
                field_dict["options"] = [
                    {"value": option_value, "name": option_name}
                    for option_value, option_name in options
                ]
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
                    "default": "cheese",
                    "type": "select",
                    "required": True,
                    "placeholder": "",
                    "instructions": "",
                    "options": [
                        {"value": "cheese", "name": "Cheese"},
                        {"value": "wine", "name": "Wine"}
                    ]
                    "restrictions": {},
                },
                {
                    "name": "comments",
                    "label": "comments",
                    "default": "",
                    "type": "text",
                    "required": False,
                    "placeholder": "Any comments?",
                    "instructions": "Please enter additional comments here."
                    "restrictions": {
                        "max_length": 200
                    }
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
        })


def shim_student_view(view_func, check_logged_in=False):
    """Create a "shim" view for a view function from the student Django app.

    Specifically, we need to:
    * Strip out enrollment params, since the client for the new registration/login
        page will communicate with the enrollment API to update enrollments.

    * Return responses with HTTP status codes indicating success/failure
        (instead of always using status 200, but setting "success" to False in
        the JSON-serialized content of the response)

    * Use status code 302 for redirects instead of
        "redirect_url" in the JSON-serialized content of the response.

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
    def _inner(request):

        # The login and registration handlers in student view try to change
        # the user's enrollment status if these parameters are present.
        # Since we want the JavaScript client to communicate directly with
        # the enrollment API, we want to prevent the student views from
        # updating enrollments.
        if "enrollment_action" in request.POST:
            del request.POST["enrollment_action"]
        if "course_id" in request.POST:
            del request.POST["course_id"]

        # Call the original view to generate a response.
        # We can safely modify the status code or content
        # of the response, but to be safe we won't mess
        # with the headers.
        response = view_func(request)

        # Most responses from this view are JSON-encoded
        # dictionaries with keys "success", "value", and
        # (sometimes) "redirect_url".
        # We want to communicate some of this information
        # using HTTP status codes instead.
        try:
            response_dict = json.loads(response.content)
            msg = response_dict.get("value", u"")
            redirect_url = response_dict.get("redirect_url") or response_dict.get("redirect")
            success = response_dict.get("success")
        except (ValueError, TypeError):
            msg = response.content
            success = True
            redirect_url = None

        # If the user is not authenticated, and we expect them to be
        # send a status 403.
        if check_logged_in and not request.user.is_authenticated():
            response.status_code = 403
            response.content = msg

        # If the view wants to redirect us, send a status 302
        elif redirect_url is not None:
            response.status_code = 302
            response.content = redirect_url

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
