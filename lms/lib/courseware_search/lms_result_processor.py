from opaque_keys.edx.locations import SlashSeparatedCourseKey
from search.views import SearchResultProcessor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.search import path_to_location

from courseware.access import has_access

class LmsSearchResultProcessor(SearchResultProcessor):

    _course_key = None
    _usage_key = None
    _module_store = None
    _module_temp_dictionary = {}

    def get_course_key(self):
        if self._course_key is None:
            self._course_key = SlashSeparatedCourseKey.from_deprecated_string(self._results_fields["course"])
        return self._course_key

    def get_usage_key(self):
        if self._usage_key is None:
            self._usage_key = self.get_course_key().make_usage_key_from_deprecated_string(self._results_fields["id"])
        return self._usage_key

    def get_module_store(self):
        if self._module_store is None:
            self._module_store = modulestore()
        return self._module_store

    def get_item(self, usage_key):
        if usage_key not in self._module_temp_dictionary:
            self._module_temp_dictionary[usage_key] = self.get_module_store().get_item(usage_key)
        return self._module_temp_dictionary[usage_key]

    @property
    def location(self):
        # TODO: update whern changes to "cohorted-courseware" branch are merged in
        (course_key, chapter, section, position) = path_to_location(self.get_module_store(), self.get_usage_key())

        def get_display_name(category, item_id):
            item = self.get_item(course_key.make_usage_key(category, item_id))
            return getattr(item, "display_name", None)

        def get_position_name(section, position):
            pos = int(position)
            section_item = self.get_item(course_key.make_usage_key('sequential', section))
            if section_item.has_children and len(section_item.children) >= pos:
                item = self.get_item(section_item.children[pos - 1])
                return getattr(item, "display_name", None)
            return None

        location_description = []
        if chapter:
            location_description.append(get_display_name('chapter', chapter))
        if section:
            location_description.append(get_display_name('sequential', section))
        if position:
            location_description.append(get_position_name(section, position))

        return location_description

    def should_remove(self, user):
        return has_access(
                user,
                'load',
                self.get_item(self.get_usage_key()),
                self.get_course_key()
            ) is False
