import logging
from itertools import groupby
from collections import Iterable

from django.db.models import Q

from models import CourseSoftware, UserLicense

log = logging.getLogger("mitx.licenses")


def get_or_create_courses_licenses(user, courses):
    user_licenses = get_courses_licenses(user, courses)

    for software, license in user_licenses.iteritems():
        if license is None:
            user_licenses[software] = get_or_create_user_license(user, software)

    log.info(user_licenses)

    return user_licenses


def get_courses_licenses(user, courses):
    course_ids = set(course.id for course in courses)
    all_software = CourseSoftware.objects.filter(course_id__in=course_ids)

    user_licenses = dict.fromkeys(all_software, None)

    assigned_licenses = UserLicense.objects.filter(software__in=all_software, user=user)
    assigned_by_software = {lic.software:lic for lic in assigned_licenses}

    for software, license in assigned_by_software.iteritems():
        user_licenses[software] = license

    return user_licenses


def get_or_create_user_license(user, software):
    license = None
    try:
        # Find a licenses associated with the user or with no user
        # associated.
        query = (Q(user__isnull=True) | Q(user=user)) & Q(software=software)

        # TODO fix a race condition in this code when more than one
        # user is getting a license assigned

        license = UserLicense.objects.filter(query)[0]

        if license.user is not user:
            license.user = user
            license.save()

    except IndexError:
        # TODO look if someone has unenrolled from the class and already has a serial number
        log.error('No serial numbers available for {0}', software)


    return license
