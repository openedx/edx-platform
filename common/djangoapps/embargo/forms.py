"""
Defines forms for providing validation of embargo admin details.
"""

from django import forms
from django.utils.translation import ugettext as _

import ipaddr

from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from embargo.models import (
    EmbargoedCourse, EmbargoedState, IPFilter,
    RestrictedCourse
)
from embargo.fixtures.country_codes import COUNTRY_CODES


class CourseKeyValidationForm(forms.ModelForm):
    """Base class for validating the "course_key" (or "course_id") field.

    The default behavior in Django admin is to:
    * Save course keys for courses that do not exist.
    * Return a 500 response if the course key format is invalid.

    Using this form ensures that we display a user-friendly
    error message instead.

    """

    def clean_course_id(self):
        """Clean the 'course_id' field in the form. """
        return self._clean_course_key("course_id")

    def clean_course_key(self):
        """Clean the 'course_key' field in the form. """
        return self._clean_course_key("course_key")

    def _clean_course_key(self, field_name):
        """Validate the course key.

        Checks that the key format is valid and that
        the course exists.  If not, displays an error message.

        Arguments:
            field_name (str): The name of the field to validate.

        Returns:
            CourseKey

        """
        cleaned_id = self.cleaned_data[field_name]
        error_msg = _('COURSE NOT FOUND.  Please check that the course ID is valid.')

        try:
            course_key = CourseKey.from_string(cleaned_id)
        except InvalidKeyError:
            raise forms.ValidationError(error_msg)

        if not modulestore().has_course(course_key):
            raise forms.ValidationError(error_msg)

        return course_key


class EmbargoedCourseForm(CourseKeyValidationForm):
    """Validate course keys for the EmbargoedCourse model. """

    class Meta:  # pylint: disable=missing-docstring
        model = EmbargoedCourse


class RestrictedCourseForm(CourseKeyValidationForm):
    """Validate course keys for the RestirctedCourse model. """

    class Meta:  # pylint: disable=missing-docstring
        model = RestrictedCourse


class EmbargoedStateForm(forms.ModelForm):  # pylint: disable=incomplete-protocol
    """Form validating entry of states to embargo"""

    class Meta:  # pylint: disable=missing-docstring
        model = EmbargoedState

    def _is_valid_code(self, code):
        """Whether or not code is a valid country code"""
        return code in COUNTRY_CODES

    def clean_embargoed_countries(self):
        """Validate the country list"""
        embargoed_countries = self.cleaned_data["embargoed_countries"]
        if not embargoed_countries:
            return ''

        error_countries = []

        for country in embargoed_countries.split(','):
            country = country.strip().upper()
            if not self._is_valid_code(country):
                error_countries.append(country)

        if error_countries:
            msg = 'COULD NOT PARSE COUNTRY CODE(S) FOR: {0}'.format(error_countries)
            msg += ' Please check the list of country codes and verify your entries.'
            raise forms.ValidationError(msg)

        return embargoed_countries


class IPFilterForm(forms.ModelForm):  # pylint: disable=incomplete-protocol
    """Form validating entry of IP addresses"""

    class Meta:  # pylint: disable=missing-docstring
        model = IPFilter

    def _is_valid_ip(self, address):
        """Whether or not address is a valid ipv4 address or ipv6 address"""
        try:
            # Is this an valid ip address?
            ipaddr.IPNetwork(address)
        except ValueError:
            return False
        return True

    def _valid_ip_addresses(self, addresses):
        """
        Checks if a csv string of IP addresses contains valid values.

        If not, raises a ValidationError.
        """
        if addresses == '':
            return ''
        error_addresses = []
        for addr in addresses.split(','):
            address = addr.strip()
            if not self._is_valid_ip(address):
                error_addresses.append(address)
        if error_addresses:
            msg = 'Invalid IP Address(es): {0}'.format(error_addresses)
            msg += ' Please fix the error(s) and try again.'
            raise forms.ValidationError(msg)

        return addresses

    def clean_whitelist(self):
        """Validates the whitelist"""
        whitelist = self.cleaned_data["whitelist"]
        return self._valid_ip_addresses(whitelist)

    def clean_blacklist(self):
        """Validates the blacklist"""
        blacklist = self.cleaned_data["blacklist"]
        return self._valid_ip_addresses(blacklist)
