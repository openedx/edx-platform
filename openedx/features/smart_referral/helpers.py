from django.contrib.auth.models import User

from lms.djangoapps.onboarding.models import UserExtendedProfile, Organization

CONTACT_EMAIL_KEY = 'contact_email'


def get_platform_contacts_and_non_platform_contacts(contacts):
    """
    Returns tuple of list first list belongs to contacts of users that are currently
    registered on our platform and second list of those contacts that are not registered.
    """
    platform_users = []
    non_platform_users = []
    for contact in contacts:
        try:
            User.objects.get(email=contact[CONTACT_EMAIL_KEY])
            platform_users.append(contact)
        except User.DoesNotExist:
            non_platform_users.append(contact)
    return platform_users, non_platform_users


def sort_contacts_by_org_and_user_domain(contact_list, user):
    """
    Returns sorted list of contacts based on two criteria first is the organization admin email domain and
    second is user email domain.
    """
    first_criteria_org_email_domain = get_email_domain(get_org_admin_email(user))
    second_criteria_user_email_domain = get_email_domain(user.email)

    return sorted(
        contact_list,
        key=lambda contact: (
            get_email_domain(contact[CONTACT_EMAIL_KEY]) == first_criteria_org_email_domain,
            get_email_domain(contact[CONTACT_EMAIL_KEY]) == second_criteria_user_email_domain
        ),
        reverse=True
    )


def get_org_admin_email(user):
    """
    Return admin email of that organization with which requested user is affiliated.
    """
    try:
        user_extended_profile = UserExtendedProfile.objects.get(user_id=user.id)
        if user_extended_profile.organization:
            org = Organization.objects.get(id=user_extended_profile.organization.id)
            return org.admin.email if org.admin else None
    except (UserExtendedProfile.DoesNotExist, Organization.DoesNotExist):
        return None


def get_email_domain(email):
    """
    Return email domain name e-g "google.com", "yahoo.com" and "outlook.com" etc by splitting email after "@".
    """
    return email.split('@')[1] if email else None
