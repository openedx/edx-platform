from opaque_keys.edx.locations import SlashSeparatedCourseKey
from search.views import SearchResultProcessor
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.search import path_to_location

class LmsSearchResultProcessor(SearchResultProcessor):

    _course_key = None
    _usage_key = None

    def get_course_key(self):
        if self._course_key is None:
            self._course_key = SlashSeparatedCourseKey.from_deprecated_string(self._results_fields["course"])
        return self._course_key

    def get_usage_key(self):
        if self._usage_key is None:
            self._usage_key = self.get_course_key().make_usage_key_from_deprecated_string(self._results_fields["id"])
        return self._usage_key

    @property
    def location(self):
        # TODO: update whern changes to "cohorted-courseware" branch are merged in
        module_store = modulestore()
        (course_key, chapter, section, position) = path_to_location(module_store, self.get_usage_key())

        def get_display_name(category, item_id):
            item = module_store.get_item(course_key.make_usage_key(category, item_id))
            return getattr(item, "display_name", None)

        def get_position_name(section, position):
            pos = int(position)
            section_item = module_store.get_item(course_key.make_usage_key('sequential', section))
            if section_item.has_children and len(section_item.children) >= pos:
                item = module_store.get_item(section_item.children[pos - 1])
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
