"""
Models for embargoing visits to certain courses by IP address.

WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py lms schemamigration embargo --auto description_of_your_change
3. Add the migration file created in edx-platform/common/djangoapps/embargo/migrations/
"""

import ipaddr

from django.db import models
from django.utils.translation import ugettext as _, ugettext_lazy

from django_countries.fields import CountryField

from config_models.models import ConfigurationModel
from xmodule_django.models import CourseKeyField, NoneToEmptyManager

from embargo.messages import ENROLL_MESSAGES, COURSEWARE_MESSAGES


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


class RestrictedCourse(models.Model):
    """Course with access restrictions.

    Restricted courses can block users at two points:

    1) When enrolling in a course.
    2) When attempting to access a course the user is already enrolled in.

    The second case can occur when new restrictions
    are put into place; for example, when new countries
    are embargoed.

    Restricted courses can be configured to display
    messages to users when they are blocked.
    These displayed on pages served by the embargo app.

    """
    ENROLL_MSG_KEY_CHOICES = tuple([
        (msg_key, msg.description)
        for msg_key, msg in ENROLL_MESSAGES.iteritems()
    ])

    COURSEWARE_MSG_KEY_CHOICES = tuple([
        (msg_key, msg.description)
        for msg_key, msg in COURSEWARE_MESSAGES.iteritems()
    ])

    course_key = CourseKeyField(
        max_length=255, db_index=True, unique=True,
        help_text=ugettext_lazy(u"The course key for the restricted course.")
    )

    enroll_msg_key = models.CharField(
        max_length=255,
        choices=ENROLL_MSG_KEY_CHOICES,
        default='default',
        help_text=ugettext_lazy(u"The message to show when a user is blocked from enrollment.")
    )

    access_msg_key = models.CharField(
        max_length=255,
        choices=COURSEWARE_MSG_KEY_CHOICES,
        default='default',
        help_text=ugettext_lazy(u"The message to show when a user is blocked from accessing a course.")
    )

    def __unicode__(self):
        return unicode(self.course_key)


class Country(models.Model):
    """Representation of a country.

    This is used to define country-based access rules.
    There is a data migration that creates entries for
    each country code.

    """
    country = CountryField(
        db_index=True, unique=True,
        help_text=ugettext_lazy(u"Two character ISO country code.")
    )

    def __unicode__(self):
        return u"{name} ({code})".format(
            name=unicode(self.country.name),
            code=unicode(self.country)
        )

    class Meta:
        # Default ordering is ascending by country code
        ordering = ['country']


class CountryAccessRule(models.Model):
    """Course access rule based on the user's country.

    The rule applies to a particular course-country pair.
    Countries can either be whitelisted or blacklisted,
    but not both.

    To determine whether a user has access to a course
    based on the user's country:

    1) Retrieve the list of whitelisted countries for the course.
    (If there aren't any, then include every possible country.)

    2) From the initial list, remove all blacklisted countries
    for the course.

    """

    RULE_TYPE_CHOICES = (
        ('whitelist', 'Whitelist (allow only these countries)'),
        ('blacklist', 'Blacklist (block these countries)'),
    )

    rule_type = models.CharField(
        max_length=255,
        choices=RULE_TYPE_CHOICES,
        default='blacklist',
        help_text=ugettext_lazy(
            u"Whether to include or exclude the given course. "
            u"If whitelist countries are specified, then ONLY users from whitelisted countries "
            u"will be able to access the course.  If blacklist countries are specified, then "
            u"users from blacklisted countries will NOT be able to access the course."
        )
    )

    restricted_course = models.ForeignKey(
        "RestrictedCourse",
        help_text=ugettext_lazy(u"The course to which this rule applies.")
    )

    country = models.ForeignKey(
        "Country",
        help_text=ugettext_lazy(u"The country to which this rule applies.")
    )

    def __unicode__(self):
        if self.rule_type == 'whitelist':
            return _(u"Whitelist {country} for {course}").format(
                course=unicode(self.restricted_course.course_key),
                country=unicode(self.country),
            )
        elif self.rule_type == 'blacklist':
            return _(u"Blacklist {country} for {course}").format(
                course=unicode(self.restricted_course.course_key),
                country=unicode(self.country),
            )

    class Meta:
        unique_together = (
            # This restriction ensures that a country is on
            # either the whitelist or the blacklist, but
            # not both (for a particular course).
            ("restricted_course", "country")
        )


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

    class IPFilterList(object):
        """
        Represent a list of IP addresses with support of networks.
        """

        def __init__(self, ips):
            self.networks = [ipaddr.IPNetwork(ip) for ip in ips]

        def __iter__(self):
            for network in self.networks:
                yield network

        def __contains__(self, ip):
            try:
                ip = ipaddr.IPAddress(ip)
            except ValueError:
                return False

            for network in self.networks:
                if network.Contains(ip):
                    return True

            return False

    @property
    def whitelist_ips(self):
        """
        Return a list of valid IP addresses to whitelist
        """
        if self.whitelist == '':
            return []
        return self.IPFilterList([addr.strip() for addr in self.whitelist.split(',')])  # pylint: disable=no-member

    @property
    def blacklist_ips(self):
        """
        Return a list of valid IP addresses to blacklist
        """
        if self.blacklist == '':
            return []
        return self.IPFilterList([addr.strip() for addr in self.blacklist.split(',')])  # pylint: disable=no-member
