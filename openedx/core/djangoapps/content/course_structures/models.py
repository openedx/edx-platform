import json
import logging

from collections import OrderedDict
from model_utils.models import TimeStampedModel

from util.models import CompressedTextField
from xmodule_django.models import CourseKeyField


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class CourseStructure(TimeStampedModel):
    course_id = CourseKeyField(max_length=255, db_index=True, unique=True, verbose_name='Course ID')

    # Right now the only thing we do with the structure doc is store it and
    # send it on request. If we need to store a more complex data model later,
    # we can do so and build a migration. The only problem with a normalized
    # data model for this is that it will likely involve hundreds of rows, and
    # we'd have to be careful about caching.
    structure_json = CompressedTextField(verbose_name='Structure JSON', blank=True, null=True)

    @property
    def structure(self):
        if self.structure_json:
            return json.loads(self.structure_json)
        return None

    @property
    def ordered_blocks(self):
        """
        Return the blocks in the order with which they're seen in the courseware. Parents are ordered before children.
        """
        if self.structure:
            ordered_blocks = OrderedDict()
            self._traverse_tree(self.structure['root'], self.structure['blocks'], ordered_blocks)
            return ordered_blocks

    def _traverse_tree(self, block, unordered_structure, ordered_blocks, parent=None):
        """
        Traverses the tree and fills in the ordered_blocks OrderedDict with the blocks in
        the order that they appear in the course.
        """
        # find the dictionary entry for the current node
        cur_block = unordered_structure[block]

        if parent:
            cur_block['parent'] = parent

        ordered_blocks[block] = cur_block

        for child_node in cur_block['children']:
            self._traverse_tree(child_node, unordered_structure, ordered_blocks, parent=block)
