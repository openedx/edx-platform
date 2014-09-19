"""Python API for user accounts.

Account information includes:
* username
* password
* email

Accounts do NOT include user profile information.

"""
from django.db import transaction
from user_api.models import User, UserProfile, Registration


@transaction.commit_on_success
def create_account(username, password, email):
    """Create a new user account.

    This will implicitly create an empty profile for the user.

    Args:
        username (unicode): The username for the new account.
        password (unicode): The user's password.
        email (unicode): The email address associated with the account.

    Returns:
        unicode: an activation code for the account.

    """
    # Create the user account, setting them to "inactive" until they activate their account.
    user = User(username=username, email=email, is_active=False)
    user.set_password(password)

    try:
        user.save()
    except IntegrityError:
        # TODO
        pass

    # Create a registration to track the activation process
    # This implicitly saves the registration.
    registration = Registration()
    registration.register(user)

    # Create an empty user profile with default values
    UserProfile(user=user).save()

    # Return the activation key, which the caller should send to the user
    return registration.activation_key


def activate_account(activation_key):
    """Activate a user's account.

    Args:
        activation_key (unicode): The activation key the user received via email.

    Returns:
        None

    """
    pass


def request_email_change(username, new_email, password):
    """Request an email change.

    Send an email to the user with an activation key,
    allowing the user to change their email address.

    Users must confirm the change before we update their information.

    Args:
        username (unicode): The username associated with the account.
        new_email (unicode): The user's new email address.
        password (unicode): The password the user entered to authorize the change.

    Returns:
        None

    """
    pass


def confirm_email_change(activation_key):
    """Confirm an email change.

    Users can confirm the change by providing an activation key
    they received via email.

    Args:
        activation_key (unicode): The activation key the user received
            when he/she requested the email change.

    Returns:
        None

    """
    pass
