import logging

from django.db import models, transaction

from student.models import User

from xmodule_django.models import CourseKeyField

log = logging.getLogger("edx.licenses")


class CourseSoftware(models.Model):
    name = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    course_id = CourseKeyField(max_length=255)

    def __unicode__(self):
        return u'{0} for {1}'.format(self.name, self.course_id)


class UserLicense(models.Model):
    software = models.ForeignKey(CourseSoftware, db_index=True)
    user = models.ForeignKey(User, null=True)
    serial = models.CharField(max_length=255)


def get_courses_licenses(user, courses):
    course_ids = set(course.id for course in courses)
    all_software = CourseSoftware.objects.filter(course_id__in=course_ids)

    assigned_licenses = UserLicense.objects.filter(software__in=all_software,
                                                   user=user)

    licenses = dict.fromkeys(all_software, None)
    for license in assigned_licenses:
        licenses[license.software] = license

    log.info(assigned_licenses)
    log.info(licenses)

    return licenses


def get_license(user, software):
    try:
        # TODO: temporary fix for when somehow a user got more that one license.
        # The proper fix should use Meta.unique_together in the UserLicense model.
        licenses = UserLicense.objects.filter(user=user, software=software)
        license = licenses[0] if licenses else None
    except UserLicense.DoesNotExist:
        license = None

    return license


def get_or_create_license(user, software):
    license = get_license(user, software)
    if license is None:
        license = _create_license(user, software)

    return license


def _create_license(user, software):
    license = None

    try:
        # find one license that has not been assigned, locking the
        # table/rows with select_for_update to prevent race conditions
        with transaction.commit_on_success():
            selected = UserLicense.objects.select_for_update()
            license = selected.filter(user__isnull=True, software=software)[0]
            license.user = user
            license.save()
    except IndexError:
        # there are no free licenses
        log.error('No serial numbers available for %s', software)
        license = None
        # TODO [rocha]look if someone has unenrolled from the class
        # and already has a serial number

    return license
