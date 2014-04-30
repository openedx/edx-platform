"""
Models for embargoing visits to certain courses by IP address.

WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py lms schemamigration embargo --auto description_of_your_change
3. Add the migration file created in edx-platform/common/djangoapps/embargo/migrations/
"""
from django.db import models

from config_models.models import ConfigurationModel
from xmodule_django.models import CourseKeyField, NoneToEmptyManager


class EmbargoedCourse(models.Model):
    """
    Enable course embargo on a course-by-course basis.
    """
    objects = NoneToEmptyManager()

    # The course to embargo
    course_id = CourseKeyField(max_length=255, db_index=True, unique=True)

    # Whether or not to embargo
    embargoed = models.BooleanField(default=False)

    @classmethod
    def is_embargoed(cls, course_id):
        """
        Returns whether or not the given course id is embargoed.

        If course has not been explicitly embargoed, returns False.
        """
        try:
            record = cls.objects.get(course_id=course_id)
            return record.embargoed
        except cls.DoesNotExist:
            return False

    def __unicode__(self):
        not_em = "Not "
        if self.embargoed:
            not_em = ""
        # pylint: disable=no-member
        return u"Course '{}' is {}Embargoed".format(self.course_id.to_deprecated_string(), not_em)


class EmbargoedState(ConfigurationModel):
    """
    Register countries to be embargoed.
    """
    # The countries to embargo
    embargoed_countries = models.TextField(
        blank=True,
        help_text="A comma-separated list of country codes that fall under U.S. embargo restrictions"
    )

    @property
    def embargoed_countries_list(self):
        """
        Return a list of upper case country codes
        """
        if self.embargoed_countries == '':
            return []
        return [country.strip().upper() for country in self.embargoed_countries.split(',')]  # pylint: disable=no-member


class IPFilter(ConfigurationModel):
    """
    Register specific IP addresses to explicitly block or unblock.
    """
    whitelist = models.TextField(
        blank=True,
        help_text="A comma-separated list of IP addresses that should not fall under embargo restrictions."
    )

    blacklist = models.TextField(
        blank=True,
        help_text="A comma-separated list of IP addresses that should fall under embargo restrictions."
    )

    @property
    def whitelist_ips(self):
        """
        Return a list of valid IP addresses to whitelist
        """
        if self.whitelist == '':
            return []
        return [addr.strip() for addr in self.whitelist.split(',')]  # pylint: disable=no-member

    @property
    def blacklist_ips(self):
        """
        Return a list of valid IP addresses to blacklist
        """
        if self.blacklist == '':
            return []
        return [addr.strip() for addr in self.blacklist.split(',')]  # pylint: disable=no-member
