"""
Defines forms for providing validation of embargo admin details.
"""

from django import forms

from embargo.models import EmbargoedCourse, EmbargoedState, IPFilter
from embargo.fixtures.country_codes import COUNTRY_CODES

import socket

from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from xmodule.modulestore.locations import SlashSeparatedCourseKey


class EmbargoedCourseForm(forms.ModelForm):  # pylint: disable=incomplete-protocol
    """Form providing validation of entered Course IDs."""

    class Meta:  # pylint: disable=missing-docstring
        model = EmbargoedCourse

    def clean_course_id(self):
        """Validate the course id"""

        cleaned_id = self.cleaned_data["course_id"]

        try:
            course_id = SlashSeparatedCourseKey.from_deprecated_string(cleaned_id)

        except InvalidKeyError:
            msg = 'COURSE NOT FOUND'
            msg += u' --- Entered course id was: "{0}". '.format(cleaned_id)
            msg += 'Please recheck that you have supplied a valid course id.'
            raise forms.ValidationError(msg)

        # Try to get the course.  If this returns None, it's not a real course
        try:
            course = modulestore().get_course(course_id)
        except ValueError:
            msg = 'COURSE NOT FOUND'
            msg += u' --- Entered course id was: "{0}". '.format(course_id.to_deprecated_string())
            msg += 'Please recheck that you have supplied a valid course id.'
            raise forms.ValidationError(msg)
        if not course:
            msg = 'COURSE NOT FOUND'
            msg += u' --- Entered course id was: "{0}". '.format(course_id.to_deprecated_string())
            msg += 'Please recheck that you have supplied a valid course id.'
            raise forms.ValidationError(msg)

        return course_id


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

    def _is_valid_ipv4(self, address):
        """Whether or not address is a valid ipv4 address"""
        try:
            # Is this an ipv4 address?
            socket.inet_pton(socket.AF_INET, address)
        except socket.error:
            return False
        return True

    def _is_valid_ipv6(self, address):
        """Whether or not address is a valid ipv6 address"""
        try:
            # Is this an ipv6 address?
            socket.inet_pton(socket.AF_INET6, address)
        except socket.error:
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
            if not (self._is_valid_ipv4(address) or self._is_valid_ipv6(address)):
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
