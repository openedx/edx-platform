"""
Models used for robust grading.

Robust grading allows student scores to be saved per-subsection independent
of any changes that may occur to the course after the score is achieved.
We also persist students' course-level grades, and update them whenever
a student's score or the course grading policy changes. As they are
persisted, course grades are also immune to changes in course content.
"""

from base64 import b64encode
from collections import namedtuple
from hashlib import sha1
import json
from lazy import lazy
import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now
from model_utils.models import TimeStampedModel

from coursewarehistoryextended.fields import UnsignedBigIntAutoField
from opaque_keys.edx.keys import CourseKey, UsageKey
from openedx.core.djangoapps.xmodule_django.models import CourseKeyField, UsageKeyField


log = logging.getLogger(__name__)


BLOCK_RECORD_LIST_VERSION = 1

# Used to serialize information about a block at the time it was used in
# grade calculation.
BlockRecord = namedtuple('BlockRecord', ['locator', 'weight', 'raw_possible', 'graded'])


class BlockRecordList(tuple):
    """
    An immutable ordered list of BlockRecord objects.
    """

    def __new__(cls, blocks, course_key, version=None):  # pylint: disable=unused-argument
        return super(BlockRecordList, cls).__new__(cls, blocks)

    def __init__(self, blocks, course_key, version=None):
        super(BlockRecordList, self).__init__(blocks)
        self.course_key = course_key
        self.version = version or BLOCK_RECORD_LIST_VERSION

    def __eq__(self, other):
        assert isinstance(other, BlockRecordList)
        return hash(self) == hash(other)

    def __hash__(self):
        """
        Returns an integer Type value of the hash of this
        list of block records, as required by python.
        """
        return hash(self.hash_value)

    @lazy
    def hash_value(self):
        """
        Returns a hash value of the list of block records.

        This currently hashes using sha1, and returns a base64 encoded version
        of the binary digest.  In the future, different algorithms could be
        supported by adding a label indicated which algorithm was used, e.g.,
        "sha256$j0NDRmSPa5bfid2pAcUXaxCm2Dlh3TwayItZstwyeqQ=".
        """
        return b64encode(sha1(self.json_value).digest())

    @lazy
    def json_value(self):
        """
        Return a JSON-serialized version of the list of block records, using a
        stable ordering.
        """
        list_of_block_dicts = [block._asdict() for block in self]
        for block_dict in list_of_block_dicts:
            block_dict['locator'] = unicode(block_dict['locator'])  # BlockUsageLocator is not json-serializable
        data = {
            u'blocks': list_of_block_dicts,
            u'course_key': unicode(self.course_key),
            u'version': self.version,
        }
        return json.dumps(
            data,
            separators=(',', ':'),  # Remove spaces from separators for more compact representation
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, blockrecord_json):
        """
        Return a BlockRecordList from previously serialized json.
        """
        data = json.loads(blockrecord_json)
        course_key = CourseKey.from_string(data['course_key'])
        block_dicts = data['blocks']
        record_generator = (
            BlockRecord(
                locator=UsageKey.from_string(block["locator"]).replace(course_key=course_key),
                weight=block["weight"],
                raw_possible=block["raw_possible"],
                graded=block["graded"],
            )
            for block in block_dicts
        )
        return cls(record_generator, course_key, version=data['version'])

    @classmethod
    def from_list(cls, blocks, course_key):
        """
        Return a BlockRecordList from the given list and course_key.
        """
        return cls(blocks, course_key)


class VisibleBlocksQuerySet(models.QuerySet):
    """
    A custom QuerySet representing VisibleBlocks.
    """

    def create_from_blockrecords(self, blocks):
        """
        Creates a new VisibleBlocks model object.

        Argument 'blocks' should be a BlockRecordList.
        """
        model, _ = self.get_or_create(
            hashed=blocks.hash_value,
            defaults={u'blocks_json': blocks.json_value, u'course_id': blocks.course_key},
        )
        return model


class VisibleBlocks(models.Model):
    """
    A django model used to track the state of a set of visible blocks under a
    given subsection at the time they are used for grade calculation.

    This state is represented using an array of BlockRecord, stored
    in the blocks_json field. A hash of this json array is used for lookup
    purposes.
    """
    blocks_json = models.TextField()
    hashed = models.CharField(max_length=100, unique=True)
    course_id = CourseKeyField(blank=False, max_length=255, db_index=True)

    objects = VisibleBlocksQuerySet.as_manager()

    class Meta(object):
        app_label = "grades"

    def __unicode__(self):
        """
        String representation of this model.
        """
        return u"VisibleBlocks object - hash:{}, raw json:'{}'".format(self.hashed, self.blocks_json)

    @property
    def blocks(self):
        """
        Returns the blocks_json data stored on this model as a list of
        BlockRecords in the order they were provided.
        """
        return BlockRecordList.from_json(self.blocks_json)

    @classmethod
    def bulk_read(cls, course_key):
        """
        Reads all visible block records for the given course.

        Arguments:
            course_key: The course identifier for the desired records
        """
        return cls.objects.filter(course_id=course_key)

    @classmethod
    def bulk_create(cls, block_record_lists):
        """
        Bulk creates VisibleBlocks for the given iterator of
        BlockRecordList objects.
        """
        return cls.objects.bulk_create([
            VisibleBlocks(
                blocks_json=brl.json_value,
                hashed=brl.hash_value,
                course_id=brl.course_key,
            )
            for brl in block_record_lists
        ])

    @classmethod
    def bulk_get_or_create(cls, block_record_lists, course_key):
        """
        Bulk creates VisibleBlocks for the given iterator of
        BlockRecordList objects for the given course_key, but
        only for those that aren't already created.
        """
        existent_records = {record.hashed: record for record in cls.bulk_read(course_key)}
        non_existent_brls = {brl for brl in block_record_lists if brl.hash_value not in existent_records}
        cls.bulk_create(non_existent_brls)


class PersistentSubsectionGrade(TimeStampedModel):
    """
    A django model tracking persistent grades at the subsection level.
    """

    class Meta(object):
        app_label = "grades"
        unique_together = [
            # * Specific grades can be pulled using all three columns,
            # * Progress page can pull all grades for a given (course_id, user_id)
            # * Course staff can see all grades for a course using (course_id,)
            ('course_id', 'user_id', 'usage_key'),
        ]

    # primary key will need to be large for this table
    id = UnsignedBigIntAutoField(primary_key=True)  # pylint: disable=invalid-name

    user_id = models.IntegerField(blank=False)
    course_id = CourseKeyField(blank=False, max_length=255)

    # note: the usage_key may not have the run filled in for
    # old mongo courses.  Use the full_usage_key property
    # instead when you want to use/compare the usage_key.
    usage_key = UsageKeyField(blank=False, max_length=255)

    # Information relating to the state of content when grade was calculated
    subtree_edited_timestamp = models.DateTimeField('last content edit timestamp', blank=False)
    course_version = models.CharField('guid of latest course version', blank=True, max_length=255)

    # earned/possible refers to the number of points achieved and available to achieve.
    # graded refers to the subset of all problems that are marked as being graded.
    earned_all = models.FloatField(blank=False)
    possible_all = models.FloatField(blank=False)
    earned_graded = models.FloatField(blank=False)
    possible_graded = models.FloatField(blank=False)

    # timestamp for the learner's first attempt at content in
    # this subsection. If null, indicates no attempt
    # has yet been made.
    first_attempted = models.DateTimeField(null=True, blank=True)

    # track which blocks were visible at the time of grade calculation
    visible_blocks = models.ForeignKey(VisibleBlocks, db_column='visible_blocks_hash', to_field='hashed')

    def _is_unattempted_with_score(self):
        """
        Return True if the object has a non-zero score, but has not been
        attempted.  This is an inconsistent state, and needs to be cleaned up.
        """
        return self.first_attempted is None and any(field != 0.0 for field in (self.earned_all, self.earned_graded))

    def clean(self):
        """
        If an grade has not been attempted, but was given a non-zero score,
        raise a ValidationError.
        """
        if self._is_unattempted_with_score():
            raise ValidationError("Unattempted problems cannot have a non-zero score.")

    @property
    def full_usage_key(self):
        """
        Returns the "correct" usage key value with the run filled in.
        """
        if self.usage_key.run is None:  # pylint: disable=no-member
            return self.usage_key.replace(course_key=self.course_id)
        else:
            return self.usage_key

    def __unicode__(self):
        """
        Returns a string representation of this model.
        """
        return (
            u"{} user: {}, course version: {}, subsection: {} ({}). {}/{} graded, {}/{} all, first_attempted: {}"
        ).format(
            type(self).__name__,
            self.user_id,
            self.course_version,
            self.usage_key,
            self.visible_blocks_id,
            self.earned_graded,
            self.possible_graded,
            self.earned_all,
            self.possible_all,
            self.first_attempted,
        )

    @classmethod
    def read_grade(cls, user_id, usage_key):
        """
        Reads a grade from database

        Arguments:
            user_id: The user associated with the desired grade
            usage_key: The location of the subsection associated with the desired grade

        Raises PersistentSubsectionGrade.DoesNotExist if applicable
        """
        return cls.objects.select_related('visible_blocks').get(
            user_id=user_id,
            course_id=usage_key.course_key,  # course_id is included to take advantage of db indexes
            usage_key=usage_key,
        )

    @classmethod
    def bulk_read_grades(cls, user_id, course_key):
        """
        Reads all grades for the given user and course.

        Arguments:
            user_id: The user associated with the desired grades
            course_key: The course identifier for the desired grades
        """
        return cls.objects.select_related('visible_blocks').filter(
            user_id=user_id,
            course_id=course_key,
        )

    @classmethod
    def update_or_create_grade(cls, **params):
        """
        Wrapper for objects.update_or_create.
        """
        cls._prepare_params_and_visible_blocks(params)

        user_id = params.pop('user_id')
        usage_key = params.pop('usage_key')
        attempted = params.pop('attempted')

        grade, _ = cls.objects.update_or_create(
            user_id=user_id,
            course_id=usage_key.course_key,
            usage_key=usage_key,
            defaults=params,
        )
        if attempted and not grade.first_attempted:
            grade.first_attempted = now()
            grade.save()
        grade.full_clean()
        return grade

    @classmethod
    def create_grade(cls, **params):
        """
        Wrapper for objects.create.
        """
        cls._prepare_params_and_visible_blocks(params)
        cls._prepare_attempted_for_create(params, now())
        grade = cls(**params)
        grade.full_clean()
        grade.save()
        return grade

    @classmethod
    def bulk_create_grades(cls, grade_params_iter, course_key):
        """
        Bulk creation of grades.
        """
        if not grade_params_iter:
            return

        map(cls._prepare_params, grade_params_iter)
        VisibleBlocks.bulk_get_or_create([params['visible_blocks'] for params in grade_params_iter], course_key)
        map(cls._prepare_params_visible_blocks_id, grade_params_iter)
        first_attempt_timestamp = now()
        for params in grade_params_iter:
            cls._prepare_attempted_for_create(params, first_attempt_timestamp)
        grades = [PersistentSubsectionGrade(**params) for params in grade_params_iter]
        for grade in grades:
            grade.full_clean()
        return cls.objects.bulk_create(grades)

    @classmethod
    def _prepare_params_and_visible_blocks(cls, params):
        """
        Prepares the fields for the grade record, while
        creating the related VisibleBlocks, if needed.
        """
        cls._prepare_params(params)
        params['visible_blocks'] = VisibleBlocks.objects.create_from_blockrecords(params['visible_blocks'])

    @classmethod
    def _prepare_params(cls, params):
        """
        Prepares the fields for the grade record.
        """
        if not params.get('course_id', None):
            params['course_id'] = params['usage_key'].course_key
        params['course_version'] = params.get('course_version', None) or ""
        params['visible_blocks'] = BlockRecordList.from_list(params['visible_blocks'], params['course_id'])

    @classmethod
    def _prepare_attempted_for_create(cls, params, timestamp):
        """
        When creating objects, an attempted subsection gets its timestamp set
        unconditionally.
        """
        if params.pop('attempted'):
            params['first_attempted'] = timestamp

    @classmethod
    def _prepare_params_visible_blocks_id(cls, params):
        """
        Prepares the visible_blocks_id field for the grade record,
        using the hash of the visible_blocks field.  Specifying
        the hashed field eliminates extra queries to get the
        VisibleBlocks record.  Use this variation of preparing
        the params when you are sure of the existence of the
        VisibleBlock.
        """
        params['visible_blocks_id'] = params['visible_blocks'].hash_value
        del params['visible_blocks']


class PersistentCourseGrade(TimeStampedModel):
    """
    A django model tracking persistent course grades.
    """

    class Meta(object):
        app_label = "grades"
        # Indices:
        # (course_id, user_id) for individual grades
        # (course_id) for instructors to see all course grades, implicitly created via the unique_together constraint
        # (user_id) for course dashboard; explicitly declared as an index below
        # (passed_timestamp, course_id) for tracking when users first earned a passing grade.
        unique_together = [
            ('course_id', 'user_id'),
        ]
        index_together = [
            ('passed_timestamp', 'course_id'),
        ]

    # primary key will need to be large for this table
    id = UnsignedBigIntAutoField(primary_key=True)  # pylint: disable=invalid-name
    user_id = models.IntegerField(blank=False, db_index=True)
    course_id = CourseKeyField(blank=False, max_length=255)

    # Information relating to the state of content when grade was calculated
    course_edited_timestamp = models.DateTimeField(u'Last content edit timestamp', blank=False)
    course_version = models.CharField(u'Course content version identifier', blank=True, max_length=255)
    grading_policy_hash = models.CharField(u'Hash of grading policy', blank=False, max_length=255)

    # Information about the course grade itself
    percent_grade = models.FloatField(blank=False)
    letter_grade = models.CharField(u'Letter grade for course', blank=False, max_length=255)

    # Information related to course completion
    passed_timestamp = models.DateTimeField(u'Date learner earned a passing grade', blank=True, null=True)

    def __unicode__(self):
        """
        Returns a string representation of this model.
        """
        return u', '.join([
            u"{} user: {}".format(type(self).__name__, self.user_id),
            u"course version: {}".format(self.course_version),
            u"grading policy: {}".format(self.grading_policy_hash),
            u"percent grade: {}%".format(self.percent_grade),
            u"letter grade: {}".format(self.letter_grade),
            u"passed timestamp: {}".format(self.passed_timestamp),
        ])

    @classmethod
    def read_course_grade(cls, user_id, course_id):
        """
        Reads a grade from database

        Arguments:
            user_id: The user associated with the desired grade
            course_id: The id of the course associated with the desired grade

        Raises PersistentCourseGrade.DoesNotExist if applicable
        """
        return cls.objects.get(user_id=user_id, course_id=course_id)

    @classmethod
    def update_or_create_course_grade(cls, user_id, course_id, **kwargs):
        """
        Creates a course grade in the database.
        Returns a PersistedCourseGrade object.
        """
        passed = kwargs.pop('passed')
        if kwargs.get('course_version', None) is None:
            kwargs['course_version'] = ""

        grade, _ = cls.objects.update_or_create(
            user_id=user_id,
            course_id=course_id,
            defaults=kwargs
        )
        if passed and not grade.passed_timestamp:
            grade.passed_timestamp = now()
            grade.save()
        return grade
