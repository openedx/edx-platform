import json
import logging
from collections import OrderedDict
from model_utils.models import TimeStampedModel
from util.models import CompressedTextField
from util.date_utils import strftime_localized
from base64 import b32encode

import django.db.models
from django.db.models.fields import *
from django.utils.timezone import UTC
from django.utils.translation import ugettext

from xmodule_django.models import CourseKeyField, UsageKeyField
from xmodule.modulestore.django import modulestore
from xmodule.partitions.partitions import NoSuchUserPartitionError
from xmodule.course_module import CourseFields
from xmodule.fields import Date

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

class JsonCacheField(django.db.models.Field):
    def __init__(self, *args, **kwargs):
        super(JsonCacheField, self).__init__(*args, **kwargs)

    def to_representation(self, obj):
        return obj.to_json()

    def to_internal_value(self, obj):
        return obj.from_json()

class UserPartitionListCacheField(JsonCacheField):
    pass

class GroupAccessDictCacheField(JsonCacheField):
    pass

class CourseIdListCacheField(JsonCacheField):
    pass

class CourseOverviewFields(django.db.models.Model):

    # Source: None; specific to this class
    id = CourseKeyField()
    modulestore_type = CharField(max_length=5)  # 'split', 'mongo', or 'xml'

    # TODO me: find out where these variables are from...
    # it might be InheritanceMixin and LmsBlockMixin, but those aren't in CourseDescriptor's inheritance tree
    user_partitions = UserPartitionListCacheField()
    static_asset_path = TextField()
    ispublic = BooleanField()
    visible_to_staff_only = BooleanField()
    group_access = GroupAccessDictCacheField()

    # Source: XModuleMixin (x_module.py)
    location = UsageKeyField()

    # Source: CourseFields (course_module.py)
    enrollment_start = DateField()
    enrollment_end = DateField()
    start = DateField()
    end = DateField()
    advertised_start = TextField()
    pre_requisite_courses = CourseIdListCacheField()
    end_of_course_survey_url = TextField()
    display_name = TextField()
    mobile_available = BooleanField()
    facebook_url = TextField()
    enrollment_domain = TextField()
    certificates_show_before_end = BooleanField()
    certificates_display_behavior = TextField()
    course_image = TextField()
    display_organization = TextField()
    display_coursenumber = TextField()
    invitation_only = BooleanField()
    catalog_visibility = TextField()
    social_sharing_url = TextField()
    cert_name_short = TextField()
    cert_name_long = TextField()

class CourseOverviewDescriptor(CourseOverviewFields):

    @classmethod
    def create_from_course(course):
        # TODO: when we upgrade to 1.8, delete old code and uncomment new code
        modulestore_type = modulestore().get_modulestore_type(course.id)

        # Newer, better way of building return value (should work in Django >=1.8, but has NOT yet been tested)
        '''
        res = CourseOverviewDescriptor(modulestore_type=modulestore_type)
        for field in CourseOverviewFields._meta.get_fields(include_parents=False):
            if field.name != 'modulestore_type':
                setattr(res, field.name, getattr(course, field.name))
        return res
        '''

        # Old, bad way of building return value (works in all Django versions)
        return CourseOverviewDescriptor(
            id=course.id,
            modulestore_type=modulestore_type,
            user_partitions=course.user_partitions,
            static_asset_path=course.static_asset_path,
            ispublic=course.ispublic,
            visible_to_staff_only=course.visible_to_staff_only,
            group_access=course.group_access,
            location=course.location,
            enrollment_start=course.enrollment_start,
            enrollment_end=course.enrollment_end,
            start=course.start,
            end=course.end,
            advertised_start=course.advertised_start,
            pre_requisite_courses=course.pre_requisite_courses,
            end_of_course_survey_url=course.end_of_course_survey_url,
            display_name=course.display_name,
            mobile_available=course.mobile_available,
            facebook_url=course.facebook_url,
            enrollment_domain=course.enrollment_domain,
            certificates_show_before_end = course.certificates_show_before_end,
            certificates_display_behavior=course.certificates_display_behavior,
            course_image=course.course_image,
            display_organization=course.display_organization,
            display_coursenumber=course.display_coursenumber,
            invitation_only=course.invitation_only,
            catalog_visibility=course.catalog_visibility,
            social_sharing_url=course.social_sharing_url,
            cert_name_short=course.cert_name_short,
            cert_name_long=course.cert_name_long
        )

    # TODO me: find out where these methods are from...
    # it might be LmsBlockMixin, but it isn't in CourseDescriptor's inheritance tree

    @property
    def merged_group_access(self):
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

    # Source XModuleMixin

    @property
    def url_name(self):
        return self.location.name

    @property
    def display_name_with_default(self):
        """
        Return a display name for the module: use display_name if defined in
        metadata, otherwise convert the url name.
        """
        name = self.display_name
        if name is None:
            name = self.url_name.replace('_', ' ')
        return name.replace('<', '&lt;').replace('>', '&gt;')

    # Source: CourseDescriptor

    def may_certify(self):
        """
        Return True if it is acceptable to show the student a certificate download link
        """
        show_early = self.certificates_display_behavior in ('early_with_info', 'early_no_info') \
            or self.certificates_show_before_end
        return show_early or self.has_ended()

    def has_ended(self):
        """
        Returns True if the current time is after the specified course end date.
        Returns False if there is no end date specified.
        """
        if self.end is None:
            return False

        return datetime.now(UTC()) > self.end

    def has_started(self):
        return datetime.now(UTC()) > self.start

    def start_datetime_text(self, format_string="SHORT_DATE"):
        """
        Returns the desired text corresponding the course's start date and time in UTC.  Prefers .advertised_start,
        then falls back to .start
        """
        _ = ugettext
        strftime = strftime_localized

        def try_parse_iso_8601(text):
            try:
                result = Date().from_json(text)
                if result is None:
                    result = text.title()
                else:
                    result = strftime(result, format_string)
                    if format_string == "DATE_TIME":
                        result = self._add_timezone_string(result)
            except ValueError:
                result = text.title()

            return result

        if isinstance(self.advertised_start, basestring):
            return try_parse_iso_8601(self.advertised_start)
        elif self.start_date_is_still_default:
            # Translators: TBD stands for 'To Be Determined' and is used when a course
            # does not yet have an announced start date.
            return _('TBD')
        else:
            when = self.advertised_start or self.start

            if format_string == "DATE_TIME":
                return self._add_timezone_string(strftime(when, format_string))

            return strftime(when, format_string)

    @property
    def start_date_is_still_default(self):
        """
        Checks if the start date set for the course is still default, i.e. .start has not been modified,
        and .advertised_start has not been set.
        """
        return self.advertised_start is None and self.start == CourseFields.start.default

    def end_datetime_text(self, format_string="SHORT_DATE"):
        """
        Returns the end date or date_time for the course formatted as a string.

        If the course does not have an end date set (course.end is None), an empty string will be returned.
        """
        if self.end is None:
            return ''
        else:
            date_time = strftime_localized(self.end, format_string)
            return date_time if format_string == "SHORT_DATE" else self._add_timezone_string(date_time)

    @property
    def number(self):
        return self.location.course

    @property
    def display_number_with_default(self):
        """
        Return a display course number if it has been specified, otherwise return the 'course' that is in the location
        """
        if self.display_coursenumber:
            return self.display_coursenumber

        return self.number

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

def get_course_overview(course_id):
    try:
        course_overview = CourseOverviewFields.get(id=course_id)
    except CourseOverviewFields.DoesNotExist:
        course = modulestore().get_course(course_id)
        course_overview = CourseOverviewDescriptor.create_from_course(course)
        course_overview.save()
    return course_overview

# Signals must be imported in a file that is automatically loaded at app startup (e.g. models.py). We import them
# at the end of this file to avoid circular dependencies.
import signals  # pylint: disable=unused-import
