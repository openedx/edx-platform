# -*- coding: utf-8 -*-
"""
An API for client-side validation of (potential) user data.
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.user_api.accounts.api import (
    get_email_validation_error,
    get_email_existence_validation_error,
    get_password_validation_error,
    get_username_validation_error,
    get_username_existence_validation_error
)


class RegistrationValidationView(APIView):
    """
        **Use Cases**

            Get validation information about user data during registration.
            Client-side may request validation for any number of form fields,
            and the API will return a conclusion from its analysis for each
            input (i.e. valid or not valid, or a custom, detailed message).

        **Example Requests and Responses**

            - Checks the validity of the username and email inputs separately.
            POST /api/user/v1/validation/registration/
            >>> {
            >>>     "username": "hi_im_new",
            >>>     "email": "newguy101@edx.org"
            >>> }
            RESPONSE
            >>> {
            >>>     "validation_decisions": {
            >>>         "username": "",
            >>>         "email": ""
            >>>     }
            >>> }
            Empty strings indicate that there was no problem with the input.

            - Checks the validity of the password field (its validity depends
              upon both the username and password fields, so we need both). If
              only password is input, we don't check for password/username
              compatibility issues.
            POST /api/user/v1/validation/registration/
            >>> {
            >>>     "username": "myname",
            >>>     "password": "myname"
            >>> }
            RESPONSE
            >>> {
            >>>     "validation_decisions": {
            >>>         "username": "",
            >>>         "password": "Password cannot be the same as the username"
            >>>     }
            >>> }

            - Checks the validity of the username, email, and password fields
              separately, and also tells whether an account exists. The password
              field's validity depends upon both the username and password, and
              the account's existence depends upon both the username and email.
            POST /api/user/v1/validation/registration/
            >>> {
            >>>     "username": "hi_im_new",
            >>>     "email": "cto@edx.org",
            >>>     "password": "p"
            >>> }
            RESPONSE
            >>> {
            >>>     "validation_decisions": {
            >>>         "username": "",
            >>>         "email": "It looks like cto@edx.org belongs to an existing account. Try again with a different email address.",
            >>>         "password": "Password must be at least 2 characters long",
            >>>     }
            >>> }
            In this example, username is valid and (we assume) there is
            a preexisting account with that email. The password also seems
            to contain the username.

            Note that a validation decision is returned *for all* inputs, whether
            positive or negative.

        **Available Handlers**

            "username":
                A handler to check the validity of usernames.
            "email":
                A handler to check the validity of emails.
            "password":
                A handler to check the validity of passwords; a compatibility
                decision with the username is made if it exists in the input.
    """

    def username_handler(self, request):
        username = request.data.get('username')
        invalid_username_error = get_username_validation_error(username)
        username_exists_error = get_username_existence_validation_error(username)
        # Existing usernames are already valid, so we prefer that error.
        return username_exists_error or invalid_username_error

    def email_handler(self, request):
        email = request.data.get('email')
        invalid_email_error = get_email_validation_error(email)
        email_exists_error = get_email_existence_validation_error(email)
        # Existing emails are already valid, so we prefer that error.
        return email_exists_error or invalid_email_error

    def password_handler(self, request):
        username = request.data.get('username') or None
        password = request.data.get('password')
        return get_password_validation_error(password, username)

    validation_handlers = {
        "username": username_handler,
        "email": email_handler,
        "password": password_handler,
    }

    def post(self, request):
        """
        POST /api/user/v1/validation/registration/

        Expects request of the form
        >>> {
        >>>     "username": "mslm",
        >>>     "email": "mslm@gmail.com",
        >>>     "password": "password123"
        >>> }
        where each key is the appropriate form field name and the value is
        user input. One may enter individual inputs if needed. Some inputs
        can get extra verification checks if entered along with others,
        like when the password may not equal the username.
        """
        validation_decisions = {}
        for form_field_key in self.validation_handlers:
            # For every field requiring validation from the client,
            # request a decision for it from the appropriate handler.
            if form_field_key in request.data:
                handler = self.validation_handlers[form_field_key]
                validation_decisions.update({
                    form_field_key: handler(self, request)
                })
        return Response({"validation_decisions": validation_decisions})
