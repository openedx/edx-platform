"""
Programmatic integration point for User API Accounts sub-application
"""
from django.utils.translation import ugettext as _
from django.db import transaction, IntegrityError
import datetime
from pytz import UTC
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.core.validators import validate_email, validate_slug, ValidationError
from openedx.core.djangoapps.user_api.preferences.api import update_user_preferences
from openedx.core.djangoapps.user_api.errors import PreferenceValidationError

from student.models import User, UserProfile, Registration
from student import views as student_views
from util.model_utils import emit_setting_changed_event

from openedx.core.lib.api.view_utils import add_serializer_errors

from ..errors import (
    AccountUpdateError, AccountValidationError, AccountUsernameInvalid, AccountPasswordInvalid,
    AccountEmailInvalid, AccountUserAlreadyExists,
    UserAPIInternalError, UserAPIRequestError, UserNotFound, UserNotAuthorized
)
from ..forms import PasswordResetFormNoActive
from ..helpers import intercept_errors
from ..models import UserPreference

from . import (
    ACCOUNT_VISIBILITY_PREF_KEY, PRIVATE_VISIBILITY,
    EMAIL_MIN_LENGTH, EMAIL_MAX_LENGTH, PASSWORD_MIN_LENGTH, PASSWORD_MAX_LENGTH,
    USERNAME_MIN_LENGTH, USERNAME_MAX_LENGTH
)
from .serializers import (
    AccountLegacyProfileSerializer, AccountUserSerializer,
    UserReadOnlySerializer
)


@intercept_errors(UserAPIInternalError, ignore_errors=[UserAPIRequestError])
def get_account_settings(request, username=None, configuration=None, view=None):
    """Returns account information for a user serialized as JSON.

    Note:
        If `request.user.username` != `username`, this method will return differing amounts of information
        based on who `request.user` is and the privacy settings of the user associated with `username`.

    Args:
        request (Request): The request object with account information about the requesting user.
            Only the user with username `username` or users with "is_staff" privileges can get full
            account information. Other users will get the account fields that the user has elected to share.
        username (str): Optional username for the desired account information. If not specified,
            `request.user.username` is assumed.
        configuration (dict): an optional configuration specifying which fields in the account
            can be shared, and the default visibility settings. If not present, the setting value with
            key ACCOUNT_VISIBILITY_CONFIGURATION is used.
        view (str): An optional string allowing "is_staff" users and users requesting their own
            account information to get just the fields that are shared with everyone. If view is
            "shared", only shared account information will be returned, regardless of `request.user`.

    Returns:
         A dict containing account fields.

    Raises:
         UserNotFound: no user with username `username` exists (or `request.user.username` if
            `username` is not specified)
         UserAPIInternalError: the operation failed due to an unexpected error.
    """
    requesting_user = request.user

    if username is None:
        username = requesting_user.username

    try:
        existing_user = User.objects.select_related('profile').get(username=username)
    except ObjectDoesNotExist:
        raise UserNotFound()

    has_full_access = requesting_user.username == username or requesting_user.is_staff
    if has_full_access and view != 'shared':
        admin_fields = settings.ACCOUNT_VISIBILITY_CONFIGURATION.get('admin_fields')
    else:
        admin_fields = None

    return UserReadOnlySerializer(
        existing_user,
        configuration=configuration,
        custom_fields=admin_fields,
        context={'request': request}
    ).data


@intercept_errors(UserAPIInternalError, ignore_errors=[UserAPIRequestError])
def update_account_settings(requesting_user, update, username=None):
    """Update user account information.

    Note:
        It is up to the caller of this method to enforce the contract that this method is only called
        with the user who made the request.

    Arguments:
        requesting_user (User): The user requesting to modify account information. Only the user with username
            'username' has permissions to modify account information.
        update (dict): The updated account field values.
        username (str): Optional username specifying which account should be updated. If not specified,
            `requesting_user.username` is assumed.

    Raises:
        UserNotFound: no user with username `username` exists (or `requesting_user.username` if
            `username` is not specified)
        UserNotAuthorized: the requesting_user does not have access to change the account
            associated with `username`
        AccountValidationError: the update was not attempted because validation errors were found with
            the supplied update
        AccountUpdateError: the update could not be completed. Note that if multiple fields are updated at the same
            time, some parts of the update may have been successful, even if an AccountUpdateError is returned;
            in particular, the user account (not including e-mail address) may have successfully been updated,
            but then the e-mail change request, which is processed last, may throw an error.
        UserAPIInternalError: the operation failed due to an unexpected error.
    """
    if username is None:
        username = requesting_user.username

    existing_user, existing_user_profile = _get_user_and_profile(username)

    if requesting_user.username != username:
        raise UserNotAuthorized()

    # If user has requested to change email, we must call the multi-step process to handle this.
    # It is not handled by the serializer (which considers email to be read-only).
    changing_email = False
    if "email" in update:
        changing_email = True
        new_email = update["email"]
        del update["email"]

    # If user has requested to change name, store old name because we must update associated metadata
    # after the save process is complete.
    old_name = None
    if "name" in update:
        old_name = existing_user_profile.name

    # Check for fields that are not editable. Marking them read-only causes them to be ignored, but we wish to 400.
    read_only_fields = set(update.keys()).intersection(
        AccountUserSerializer.get_read_only_fields() + AccountLegacyProfileSerializer.get_read_only_fields()
    )

    # Build up all field errors, whether read-only, validation, or email errors.
    field_errors = {}

    if read_only_fields:
        for read_only_field in read_only_fields:
            field_errors[read_only_field] = {
                "developer_message": u"This field is not editable via this API",
                "user_message": _(u"The '{field_name}' field cannot be edited.").format(field_name=read_only_field)
            }
            del update[read_only_field]

    user_serializer = AccountUserSerializer(existing_user, data=update)
    legacy_profile_serializer = AccountLegacyProfileSerializer(existing_user_profile, data=update)

    for serializer in user_serializer, legacy_profile_serializer:
        field_errors = add_serializer_errors(serializer, update, field_errors)

    # If the user asked to change email, validate it.
    if changing_email:
        try:
            student_views.validate_new_email(existing_user, new_email)
        except ValueError as err:
            field_errors["email"] = {
                "developer_message": u"Error thrown from validate_new_email: '{}'".format(err.message),
                "user_message": err.message
            }

    # If we have encountered any validation errors, return them to the user.
    if field_errors:
        raise AccountValidationError(field_errors)

    try:
        # If everything validated, go ahead and save the serializers.

        # We have not found a way using signals to get the language proficiency changes (grouped by user).
        # As a workaround, store old and new values here and emit them after save is complete.
        if "language_proficiencies" in update:
            old_language_proficiencies = legacy_profile_serializer.data["language_proficiencies"]

        for serializer in user_serializer, legacy_profile_serializer:
            serializer.save()

        # if any exception is raised for user preference (i.e. account_privacy), the entire transaction for user account
        # patch is rolled back and the data is not saved
        if 'account_privacy' in update:
            update_user_preferences(
                requesting_user, {'account_privacy': update["account_privacy"]}, existing_user
            )

        if "language_proficiencies" in update:
            new_language_proficiencies = update["language_proficiencies"]
            emit_setting_changed_event(
                user=existing_user,
                db_table=existing_user_profile.language_proficiencies.model._meta.db_table,
                setting_name="language_proficiencies",
                old_value=old_language_proficiencies,
                new_value=new_language_proficiencies,
            )

        # If the name was changed, store information about the change operation. This is outside of the
        # serializer so that we can store who requested the change.
        if old_name:
            meta = existing_user_profile.get_meta()
            if 'old_names' not in meta:
                meta['old_names'] = []
            meta['old_names'].append([
                old_name,
                u"Name change requested through account API by {0}".format(requesting_user.username),
                datetime.datetime.now(UTC).isoformat()
            ])
            existing_user_profile.set_meta(meta)
            existing_user_profile.save()

    except PreferenceValidationError as err:
        raise AccountValidationError(err.preference_errors)
    except Exception as err:
        raise AccountUpdateError(
            u"Error thrown when saving account updates: '{}'".format(err.message)
        )

    # And try to send the email change request if necessary.
    if changing_email:
        try:
            student_views.do_email_change_request(existing_user, new_email)
        except ValueError as err:
            raise AccountUpdateError(
                u"Error thrown from do_email_change_request: '{}'".format(err.message),
                user_message=err.message
            )


def _get_user_and_profile(username):
    """
    Helper method to return the legacy user and profile objects based on username.
    """
    try:
        existing_user = User.objects.get(username=username)
        existing_user_profile = UserProfile.objects.get(user=existing_user)
    except ObjectDoesNotExist:
        raise UserNotFound()

    return existing_user, existing_user_profile


@intercept_errors(UserAPIInternalError, ignore_errors=[UserAPIRequestError])
@transaction.atomic
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
        UserAPIInternalError: the operation failed due to an unexpected error.
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


@intercept_errors(UserAPIInternalError, ignore_errors=[UserAPIRequestError])
def activate_account(activation_key):
    """Activate a user's account.

    Args:
        activation_key (unicode): The activation key the user received via email.

    Returns:
        None

    Raises:
        UserNotAuthorized
        UserAPIInternalError: the operation failed due to an unexpected error.
    """
    try:
        registration = Registration.objects.get(activation_key=activation_key)
    except Registration.DoesNotExist:
        raise UserNotAuthorized
    else:
        # This implicitly saves the registration
        registration.activate()


@intercept_errors(UserAPIInternalError, ignore_errors=[UserAPIRequestError])
def request_password_change(email, orig_host, is_secure):
    """Email a single-use link for performing a password reset.

    Users must confirm the password change before we update their information.

    Args:
        email (str): An email address
        orig_host (str): An originating host, extracted from a request with get_host
        is_secure (bool): Whether the request was made with HTTPS

    Returns:
        None

    Raises:
        UserNotFound
        AccountRequestError
        UserAPIInternalError: the operation failed due to an unexpected error.
    """
    # Binding data to a form requires that the data be passed as a dictionary
    # to the Form class constructor.
    form = PasswordResetFormNoActive({'email': email})

    # Validate that a user exists with the given email address.
    if form.is_valid():
        # Generate a single-use link for performing a password reset
        # and email it to the user.
        form.save(
            from_email=settings.DEFAULT_FROM_EMAIL,
            domain_override=orig_host,
            use_https=is_secure
        )
    else:
        # No user with the provided email address exists.
        raise UserNotFound


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
