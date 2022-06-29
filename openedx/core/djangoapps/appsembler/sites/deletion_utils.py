"""
Site and courses deletion utils.
"""

import beeline

from django.apps import apps
from django.core.management import CommandError
from django.db import transaction

import tahoe_sites.api
from organizations.models import OrganizationCourse


from opaque_keys.edx.django.models import CourseKeyField, LearningContextKeyField

from common.djangoapps.util.organizations_helpers import get_organization_courses


from ...content.course_overviews.models import CourseOverview
from organizations.api import get_organization_courses


def confirm_deletion(commit, question):
    """
    Utility for yes/no interactive confirmation if `commit` is `None`.
    """
    if commit is None:
        result = input('%s [type yes or no] ' % question)
        while not result or result.lower() not in ['yes', 'no']:
            result = input('Please answer yes or no: ')
        return result == 'yes'
    return commit


def remove_course_creator_role(users):
    """
    Remove course creator role to fix `delete_site` issue.

    This will fail in when running tests from within the LMS because the CMS migrations
    don't run during tests. Patch this function to avoid such errors.
    TODO: RED-2853 Remove this helper when AMC is removed
          This helper is being replaced by `update_course_creator_role_for_cms` which has unit tests.
    """
    from cms.djangoapps.course_creators.models import CourseCreator  # Fix LMS->CMS imports.
    from student.roles import CourseAccessRole  # Avoid circular import.
    CourseCreator.objects.filter(user__in=users).delete()
    CourseAccessRole.objects.filter(user__in=users).delete()


@beeline.traced(name="delete_site")
def delete_site(site):
    """
    Delete site with all related objects except for MongoDB course files.
    """
    from third_party_auth.models import SAMLConfiguration  # local import to avoid import-time errors

    print('Deleting SiteConfiguration of', site)
    site.configuration.delete()

    print('Deleting theme of', site)
    site.themes.all().delete()

    organization = tahoe_sites.api.get_organization_by_site(site)

    print('Deleting users of', site)
    users = tahoe_sites.api.get_users_of_organization(organization, without_inactive_users=False)
    remove_course_creator_role(users)

    # Prepare removing users by avoiding on_delete=models.PROTECT error
    # SAMLConfiguration will be deleted with `site.delete()`
    SAMLConfiguration.objects.filter(changed_by__in=users).update(changed_by=None)

    users.delete()

    print('Deleting courses of', site)
    delete_organization_courses(organization)

    print('Deleting organization', organization)
    organization.delete()

    print('Deleting site', site)
    site.delete()


def get_models_using_course_key():
    """
    Get all course related model classes.
    """
    course_key_field_names = {
        'course_key',
        'course_id',
    }

    models_with_course_key = {
        (CourseOverview, 'id'),  # The CourseKeyField with a `id` name. Hard-coding it for simplicity.
        (OrganizationCourse, 'course_id'),  # course_id is CharField
    }

    model_classes = apps.get_models()
    for model_class in model_classes:
        for field_name in course_key_field_names:
            field_object = getattr(model_class, field_name, None)
            if field_object:
                field_definition = getattr(field_object, 'field', None)
                if field_definition and isinstance(field_definition, (CourseKeyField, LearningContextKeyField)):
                    models_with_course_key.add(
                        (model_class, field_name,)
                    )

    return models_with_course_key


def delete_organization_courses(organization):
    """
    Delete all course related model instances.
    """
    course_keys = []

    for course in get_organization_courses({'id': organization.id}):
        course_keys.append(course['course_id'])

    delete_related_models_of_courses(course_keys)


def delete_related_models_of_courses(course_keys):
    model_classes = get_models_using_course_key()

    print('Deleting course related models:', ', '.join([
        '{model}.{field}'.format(model=model_class.__name__, field=field_name)
        for model_class, field_name in model_classes
    ]))

    for model_class, field_name in model_classes:
        objects_to_delete = model_class.objects.filter(**{
            '{field_name}__in'.format(field_name=field_name): course_keys,
        })
        objects_to_delete.delete()


def get_courses_keys_without_organization_linked(limit=None, only_active_links=True):
    """
    Get keys of stray courses.
    """
    course_links = OrganizationCourse.objects.all()
    if only_active_links:
        course_links = course_links.filter(active=True)

    queryset = CourseOverview.objects.exclude(
        id__in=course_links.values_list('course_id', flat=True),
    )

    course_keys = queryset.values_list(
        'id', flat=True
    )

    course_keys_list = [str(course_key) for course_key in course_keys]
    if limit:
        course_keys_list = course_keys_list[:limit]

    return course_keys_list


def remove_stray_courses_from_mysql(limit, commit=None, print_func=print):
    """
    Removes courses without linked organization from LMS MySQL database.

    The MongoDB courses won't be removed with this command.
    """
    course_keys = get_courses_keys_without_organization_linked(limit=limit)
    if not course_keys:
        raise CommandError('No courses to delete.')

    print_func('Preparing to delete:')
    print_func('\n'.join(course_keys))

    commit = confirm_deletion(commit=commit, question='Do you confirm to delete those courses from the LMS?')

    with transaction.atomic():
        delete_related_models_of_courses(course_keys)
        print_func('Finished [commit={}] courses.'.format(commit))

        if not commit:
            transaction.set_rollback(True)
