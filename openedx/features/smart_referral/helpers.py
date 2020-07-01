from django.contrib.auth.models import User

from lms.djangoapps.onboarding.models import UserExtendedProfile

from .models import SmartReferral

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
        user_org = user_extended_profile.organization
        if user_org and user_org.admin:
            return user_org.admin.email
    except UserExtendedProfile.DoesNotExist:
        return None


def get_email_domain(email):
    """
    Return email domain name e.g "google.com", "yahoo.com" and "outlook.com" etc by splitting email after "@".
    """
    return email.split('@')[1] if email else None


def filter_referred_contacts(contacts, user):
    """
    Filter out contacts which are already been referred twice or which are referred by current user.
    """
    if not contacts:
        return None

    filtered_contacts = []
    for contact in contacts:
        queryset_referral = SmartReferral.objects.filter(contact_email=contact.get('contact_email'))
        queryset_count = queryset_referral.count()
        is_referred_before = queryset_count > 1 or (queryset_count == 1 and queryset_referral.first().user == user)
        filtered_contacts.append(contact) if not is_referred_before else None

    return filtered_contacts
