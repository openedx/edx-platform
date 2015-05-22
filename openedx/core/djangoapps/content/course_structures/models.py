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

import django
from base64 import b32encode
from django.db.models.fields import *


class CourseOverviewCacheModel(django.db.models.Model):

    # Source: CourseFields
    enrollment_start = DateField()
    enrollment_end = DateField()
    start = DateField()
    end = DateField()
    pre_requisite_courses = TextField()  # JSON representation of a list of course keys
    end_of_course_survey_url = TextField()
    display_name = TextField()
    mobile_available = BooleanField()
    facebook_url = TextField()
    enrollment_domain = TextField()
    certificates_display_behavior = TextField()
    display_organization = TextField()
    display_coursenumber = TextField()
    invitation_only = BooleanField()
    catalog_visibility = TextField()

    # Source: InheritanceMixin
    user_partitions = TextField()  # JSON representation of a UserPartitionList

    # Source: XModuleMixin
    location = CharField(max_length=255)  # TODO: confirm this is the correct way to store

    # Source: LmsBlockMixin
    ispublic = BooleanField()
    visible_to_staff_only = BooleanField()
    group_access = TextField()  # JSON represnetation of a GroupAccessDict

class CourseOverview(CourseOverviewFields):

    # Source: LmsBlockMixin

    @property
    def merged_group_access(self):
        # TODO: confirm simplifying assumption that self.get_parent() is None
        return self.group_access or {}

    def _get_user_partition(self, user_partition_id):
        """
        Returns the user partition with the specified id.  Raises
        `NoSuchUserPartitionError` if the lookup fails.
        """
        for user_partition in self.user_partitions:
            if user_partition.id == user_partition_id:
                return user_partition

        raise NoSuchUserPartitionError("could not find a UserPartition with ID [{}]".format(user_partition_id))

    # Source:

    def has_ended(self):
        """
        Returns True if the current time is after the specified course end date.
        Returns False if there is no end date specified.
        """
        if self.end is None:
            return False

        return datetime.now(UTC()) > self.end

    @property
    def number(self):
        return self.location.course


    def may_certify(self):
        """
        Return True if it is acceptable to show the student a certificate download link
        """
        show_early = self.certificates_display_behavior in ('early_with_info', 'early_no_info') or self.certificates_show_before_end
        return show_early or self.has_ended()

    def has_started(self):
        return datetime.now(UTC()) > self.start

    @property
    def display_number_with_default(self):
        """
        Return a display course number if it has been specified, otherwise return the 'course' that is in the location
        """
        if self.display_coursenumber:
            return self.display_coursenumber

        return self.number

    @property
    def number(self):
        return self.location.course

    @property
    def id(self):
        """Return the course_id for this course"""
        return self.location.course_key

    @property
    def org(self):
        return self.location.org

    @property
    def display_org_with_default(self):
        """
        Return a display organization if it has been specified, otherwise return the 'org' that is in the location
        """
        if self.display_organization:
            return self.display_organization

        return self.org


    def clean_id(self, padding_char='='):
        """
        Returns a unique deterministic base32-encoded ID for the course.
        The optional padding_char parameter allows you to override the "=" character used for padding.
        """
        return "course_{}".format(
            b32encode(unicode(self.location.course_key)).replace('=', padding_char)
        )

# Signals must be imported in a file that is automatically loaded at app startup (e.g. models.py). We import them
# at the end of this file to avoid circular dependencies.
import signals  # pylint: disable=unused-import
