"""
Python API for user accounts.

Account information includes:
* username
* password
* email

Accounts do NOT include user profile information.

"""


def create_account(username, password, email):
    """
    Create a new user account.
    This will implicitly create an empty profile for the user.

    Args:
        username (unicode): The username for the new account.
        password (unicode): The user's password.
        email (unicode): The email address associated with the account.

    Returns:
        None

    """
    pass


def request_email_change(username, new_email, password):
    """
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
    """
    Confirm an email change.  Users can confirm the change by providing
    an activation key they received via email.

    Args:
        activation_key (unicode): The activation key the user received
            when he/she requested the email change.

    Returns:
        None

    """
    pass
