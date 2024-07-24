import logging

from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore as ModuleStore

log = logging.getLogger(__name__)


class CoursewareContent:
    def prepare_data(self, item, structure_key):
        location_info = {
            "course": str(structure_key),
            "org": structure_key.org,
            "item_id": item.scope_ids.usage_id.block_id,
            "usage_key": str(item.scope_ids.usage_id)
        }
        _index_dictionary = item.index_dictionary()
        _index_dictionary.update(location_info)
        children = []
        if item.has_children:
            for child_item in item.get_children():
                children.extend(self.prepare_data(child_item, structure_key))

        return [_index_dictionary] + children

    def fetch_course_blocks(self, modulestore, course_key):
        blocks = []
        with modulestore.branch_setting(ModuleStoreEnum.RevisionOption.published_only):
            structure = modulestore.get_course(course_key, depth=None)

            for item in structure.get_children():
                blocks.extend(self.prepare_data(item, course_key))
        return blocks

    def fetch(self, course_key=None, *args, **kwargs):
        modulestore = ModuleStore()
        if not course_key:
            course_keys = CourseOverview.objects.values_list('id', flat=True)
        elif course_key:
            course_keys = [CourseKey.from_string(course_key)]
        all_blocks = []
        for course_id in course_keys:
            all_blocks.extend(self.fetch_course_blocks(modulestore, course_id))
        return all_blocks
