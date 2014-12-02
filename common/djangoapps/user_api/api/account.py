"""Python API for user accounts.


Account information includes a student's username, password, and email
address, but does NOT include user profile information (i.e., demographic
information and preferences).

"""
from django.conf import settings
from django.db import transaction, IntegrityError
from django.core.validators import validate_email, validate_slug, ValidationError
from django.contrib.auth.forms import PasswordResetForm

from user_api.models import User, UserProfile, Registration, PendingEmailChange
from user_api.helpers import intercept_errors


USERNAME_MIN_LENGTH = 2
USERNAME_MAX_LENGTH = 30

EMAIL_MIN_LENGTH = 3
EMAIL_MAX_LENGTH = 254

PASSWORD_MIN_LENGTH = 2
PASSWORD_MAX_LENGTH = 75


class AccountRequestError(Exception):
    """There was a problem with the request to the account API. """
    pass


class AccountInternalError(Exception):
    """An internal error occurred in the account API. """
    pass


class AccountUserAlreadyExists(AccountRequestError):
    """User with the same username and/or email already exists. """
    pass


class AccountUsernameAlreadyExists(AccountUserAlreadyExists):
    """An account already exists with the requested username. """
    pass


class AccountEmailAlreadyExists(AccountUserAlreadyExists):
    """An account already exists with the requested email. """
    pass


class AccountUsernameInvalid(AccountRequestError):
    """The requested username is not in a valid format. """
    pass


class AccountEmailInvalid(AccountRequestError):
    """The requested email is not in a valid format. """
    pass


class AccountPasswordInvalid(AccountRequestError):
    """The requested password is not in a valid format. """
    pass


class AccountUserNotFound(AccountRequestError):
    """The requested user does not exist. """
    pass


class AccountNotAuthorized(AccountRequestError):
    """The user is not authorized to perform the requested action. """
    pass


@intercept_errors(AccountInternalError, ignore_errors=[AccountRequestError])
@transaction.commit_on_success
def create_account(username, password, email):
    """Create a new user account.

    This will implicitly create an empty profile for the user.

    WARNING: This function does NOT yet implement all the features
    in `student/views.py`.  Until it does, please use this method
    ONLY for tests of the account API, not in production code.
    In particular, these are currently missing:

    * 3rd party auth
    * External auth (shibboleth)
    * Complex password policies (ENFORCE_PASSWORD_POLICY)

    In addition, we assume that some functionality is handled
    at higher layers:

    * Analytics events
    * Activation email
    * Terms of service / honor code checking
    * Recording demographic info (use profile API)
    * Auto-enrollment in courses (if invited via instructor dash)

    Args:
        username (unicode): The username for the new account.
        password (unicode): The user's password.
        email (unicode): The email address associated with the account.

    Returns:
        unicode: an activation key for the account.

    Raises:
        AccountUserAlreadyExists
        AccountUsernameInvalid
        AccountEmailInvalid
        AccountPasswordInvalid

    """
    # Validate the username, password, and email
    # This will raise an exception if any of these are not in a valid format.
    _validate_username(username)
    _validate_password(password, username)
    _validate_email(email)

    # Create the user account, setting them to "inactive" until they activate their account.
    user = User(username=username, email=email, is_active=False)
    user.set_password(password)

    try:
        user.save()
    except IntegrityError:
        raise AccountUserAlreadyExists

    # Create a registration to track the activation process
    # This implicitly saves the registration.
    registration = Registration()
    registration.register(user)

    # Create an empty user profile with default values
    UserProfile(user=user).save()

    # Return the activation key, which the caller should send to the user
    return registration.activation_key


def check_account_exists(username=None, email=None):
    """Check whether an account with a particular username or email already exists.

    Keyword Arguments:
        username (unicode)
        email (unicode)

    Returns:
        list of conflicting fields

    Example Usage:
        >>> account_api.check_account_exists(username="bob")
        []
        >>> account_api.check_account_exists(username="ted", email="ted@example.com")
        ["email", "username"]

    """
    conflicts = []

    if email is not None and User.objects.filter(email=email).exists():
        conflicts.append("email")

    if username is not None and User.objects.filter(username=username).exists():
        conflicts.append("username")

    return conflicts


@intercept_errors(AccountInternalError, ignore_errors=[AccountRequestError])
def account_info(username):
    """Retrieve information about a user's account.

    Arguments:
        username (unicode): The username associated with the account.

    Returns:
        dict: User's account information, if the user was found.
        None: The user does not exist.

    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return None
    else:
        return {
            u'username': username,
            u'email': user.email,
            u'is_active': user.is_active,
        }


@intercept_errors(AccountInternalError, ignore_errors=[AccountRequestError])
def activate_account(activation_key):
    """Activate a user's account.

    Args:
        activation_key (unicode): The activation key the user received via email.

    Returns:
        None

    Raises:
        AccountNotAuthorized

    """
    try:
        registration = Registration.objects.get(activation_key=activation_key)
    except Registration.DoesNotExist:
        raise AccountNotAuthorized
    else:
        # This implicitly saves the registration
        registration.activate()


@intercept_errors(AccountInternalError, ignore_errors=[AccountRequestError])
def request_email_change(username, new_email, password):
    """Request an email change.

    Users must confirm the change before we update their information.

    Args:
        username (unicode): The username associated with the account.
        new_email (unicode): The user's new email address.
        password (unicode): The password the user entered to authorize the change.

    Returns:
        unicode: an activation key for the account.

    Raises:
        AccountUserNotFound
        AccountEmailAlreadyExists
        AccountEmailInvalid
        AccountNotAuthorized

    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise AccountUserNotFound

    # Check the user's credentials
    if not user.check_password(password):
        raise AccountNotAuthorized

    # Validate the email, raising an exception if it is not in the correct format
    _validate_email(new_email)

    # Verify that no active account has taken the email in between
    # the request and the activation.
    # We'll check again before confirming and persisting the change,
    # but if the email is already taken by an active account, we should
    # let the user know as soon as possible.
    if User.objects.filter(email=new_email, is_active=True).exists():
        raise AccountEmailAlreadyExists

    try:
        pending_change = PendingEmailChange.objects.get(user=user)
    except PendingEmailChange.DoesNotExist:
        pending_change = PendingEmailChange(user=user)

    # Update the change (re-using the same record if it already exists)
    # This will generate a new activation key and save the record.
    return pending_change.request_change(new_email)


@intercept_errors(AccountInternalError, ignore_errors=[AccountRequestError])
@transaction.commit_on_success
def confirm_email_change(activation_key):
    """Confirm an email change.

    Users can confirm the change by providing an activation key
    they received via email.

    Args:
        activation_key (unicode): The activation key the user received
            when he/she requested the email change.

    Returns:
        Tuple: (old_email, new_email)

    Raises:
        AccountNotAuthorized: The activation code is invalid.
        AccountEmailAlreadyExists: Someone else has already taken the email address.
        AccountInternalError

    """

    try:
        # Activation key has a uniqueness constraint, so we're guaranteed to get
        # at most one pending change.
        pending_change = PendingEmailChange.objects.select_related('user').get(
            activation_key=activation_key
        )
    except PendingEmailChange.DoesNotExist:
        # If there are no changes, then the activation key is invalid
        raise AccountNotAuthorized
    else:
        old_email = pending_change.user.email
        new_email = pending_change.new_email

        # Verify that no one else has taken the email in between
        # the request and the activation.
        # In our production database, email has a uniqueness constraint,
        # so there is no danger of a race condition here.
        if User.objects.filter(email=new_email).exists():
            raise AccountEmailAlreadyExists

        # Update the email history (in the user profile)
        try:
            profile = UserProfile.objects.get(user=pending_change.user)
        except UserProfile.DoesNotExist:
            raise AccountInternalError(
                "No profile exists for the user '{username}'".format(
                    username=pending_change.user.username
                )
            )
        else:
            profile.update_email(new_email)

        # Delete the pending change, so that the activation code
        # will be single-use
        pending_change.delete()

        # Return the old and new email
        # This allows the caller of the function to notify users at both
        # the new and old email, which is necessary for security reasons.
        return (old_email, new_email)


@intercept_errors(AccountInternalError, ignore_errors=[AccountRequestError])
def request_password_change(email, orig_host, is_secure):
    """Email a single-use link for performing a password reset.

    Users must confirm the password change before we update their information.

    Args:
        email (string): An email address
        orig_host (string): An originating host, extracted from a request with get_host
        is_secure (Boolean): Whether the request was made with HTTPS

    Returns:
        None

    Raises:
        AccountUserNotFound
        AccountRequestError

    """
    # Binding data to a form requires that the data be passed as a dictionary
    # to the Form class constructor.
    form = PasswordResetForm({'email': email})

    # Validate that an active user exists with the given email address.
    if form.is_valid():
        # Generate a single-use link for performing a password reset
        # and email it to the user.
        form.save(
            from_email=settings.DEFAULT_FROM_EMAIL,
            domain_override=orig_host,
            use_https=is_secure
        )
    else:
        # No active user with the provided email address exists.
        raise AccountUserNotFound


def _validate_username(username):
    """Validate the username.

    Arguments:
        username (unicode): The proposed username.

    Returns:
        None

    Raises:
        AccountUsernameInvalid

    """
    if not isinstance(username, basestring):
        raise AccountUsernameInvalid(u"Username must be a string")

    if len(username) < USERNAME_MIN_LENGTH:
        raise AccountUsernameInvalid(
            u"Username '{username}' must be at least {min} characters long".format(
                username=username,
                min=USERNAME_MIN_LENGTH
            )
        )
    if len(username) > USERNAME_MAX_LENGTH:
        raise AccountUsernameInvalid(
            u"Username '{username}' must be at most {max} characters long".format(
                username=username,
                max=USERNAME_MAX_LENGTH
            )
        )
    try:
        validate_slug(username)
    except ValidationError:
        raise AccountUsernameInvalid(
            u"Username '{username}' must contain only A-Z, a-z, 0-9, -, or _ characters"
        )


def _validate_password(password, username):
    """Validate the format of the user's password.

    Passwords cannot be the same as the username of the account,
    so we take `username` as an argument.

    Arguments:
        password (unicode): The proposed password.
        username (unicode): The username associated with the user's account.

    Returns:
        None

    Raises:
        AccountPasswordInvalid

    """
    if not isinstance(password, basestring):
        raise AccountPasswordInvalid(u"Password must be a string")

    if len(password) < PASSWORD_MIN_LENGTH:
        raise AccountPasswordInvalid(
            u"Password must be at least {min} characters long".format(
                min=PASSWORD_MIN_LENGTH
            )
        )

    if len(password) > PASSWORD_MAX_LENGTH:
        raise AccountPasswordInvalid(
            u"Password must be at most {max} characters long".format(
                max=PASSWORD_MAX_LENGTH
            )
        )

    if password == username:
        raise AccountPasswordInvalid(u"Password cannot be the same as the username")


def _validate_email(email):
    """Validate the format of the email address.

    Arguments:
        email (unicode): The proposed email.

    Returns:
        None

    Raises:
        AccountEmailInvalid

    """
    if not isinstance(email, basestring):
        raise AccountEmailInvalid(u"Email must be a string")

    if len(email) < EMAIL_MIN_LENGTH:
        raise AccountEmailInvalid(
            u"Email '{email}' must be at least {min} characters long".format(
                email=email,
                min=EMAIL_MIN_LENGTH
            )
        )

    if len(email) > EMAIL_MAX_LENGTH:
        raise AccountEmailInvalid(
            u"Email '{email}' must be at most {max} characters long".format(
                email=email,
                max=EMAIL_MAX_LENGTH
            )
        )

    try:
        validate_email(email)
    except ValidationError:
        raise AccountEmailInvalid(
            u"Email '{email}' format is not valid".format(email=email)
        )
