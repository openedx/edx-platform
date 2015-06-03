"""
This file contains implementation override of SearchResultProcessor which will allow
    * Blends in "location" property
    * Confirms user access to object
"""
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from search.result_processor import SearchResultProcessor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.search import path_to_location, navigation_index

from courseware.access import has_access


class LmsSearchResultProcessor(SearchResultProcessor):

    """ SearchResultProcessor for LMS Search """
    _course_key = None
    _course_name = None
    _usage_key = None
    _module_store = None
    _module_temp_dictionary = {}

    def get_course_key(self):
        """ fetch course key object from string representation - retain result for subsequent uses """
        if self._course_key is None:
            self._course_key = SlashSeparatedCourseKey.from_deprecated_string(self._results_fields["course"])
        return self._course_key

    def get_usage_key(self):
        """ fetch usage key for component from string representation - retain result for subsequent uses """
        if self._usage_key is None:
            self._usage_key = self.get_course_key().make_usage_key_from_deprecated_string(self._results_fields["id"])
        return self._usage_key

    def get_module_store(self):
        """ module store accessor - retain result for subsequent uses """
        if self._module_store is None:
            self._module_store = modulestore()
        return self._module_store

    def get_item(self, usage_key):
        """ fetch item from the modulestore - don't refetch if we've already retrieved it beforehand """
        if usage_key not in self._module_temp_dictionary:
            self._module_temp_dictionary[usage_key] = self.get_module_store().get_item(usage_key)
        return self._module_temp_dictionary[usage_key]

    @property
    def url(self):
        """
        Property to display the url for the given location, useful for allowing navigation
        """
        if "course" not in self._results_fields or "id" not in self._results_fields:
            raise ValueError("Must have course and id in order to build url")

        return reverse(
            "jump_to",
            kwargs={"course_id": self._results_fields["course"], "location": self._results_fields["id"]}
        )

    def should_remove(self, user):
        """ Test to see if this result should be removed due to access restriction """
        user_has_access = has_access(
            user,
            "load",
            self.get_item(self.get_usage_key()),
            self.get_course_key()
        )
        return not user_has_access
