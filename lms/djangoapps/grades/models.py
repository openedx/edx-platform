"""
Models used for robust grading.

Robust grading allows student scores to be saved per-subsection independent
of any changes that may occur to the course after the score is achieved.
"""

from base64 import b64encode
from collections import namedtuple
from hashlib import sha1
import json
import logging
from operator import attrgetter

from django.db import models, transaction
from django.db.utils import IntegrityError
from model_utils.models import TimeStampedModel

from coursewarehistoryextended.fields import UnsignedBigIntAutoField
from opaque_keys.edx.keys import CourseKey, UsageKey
from xmodule_django.models import CourseKeyField, UsageKeyField


log = logging.getLogger(__name__)


# Used to serialize information about a block at the time it was used in
# grade calculation.
BlockRecord = namedtuple('BlockRecord', ['locator', 'weight', 'max_score'])


class BlockRecordSet(frozenset):
    """
    An immutable ordered collection of BlockRecord objects.
    """

    def __init__(self, *args, **kwargs):
        super(BlockRecordSet, self).__init__(*args, **kwargs)
        self._json = None
        self._hash = None

    def _get_course_key_string(self):
        """
        Get the course key as a string.  All blocks are from the same course,
        so just grab one arbitrarily.  If no blocks are present, return None.
        """
        if self:
            a_block = next(iter(self))
            return unicode(a_block.locator.course_key)
        else:
            return None

    def to_json(self):
        """
        Return a JSON-serialized version of the list of block records, using a
        stable ordering.
        """
        if self._json is None:
            sorted_blocks = sorted(self, key=attrgetter('locator'))
            list_of_block_dicts = [block._asdict() for block in sorted_blocks]
            course_key_string = self._get_course_key_string()  # all blocks are from the same course

            for block_dict in list_of_block_dicts:
                block_dict['locator'] = unicode(block_dict['locator'])  # BlockUsageLocator is not json-serializable
            data = {
                'course_key': course_key_string,
                'blocks': list_of_block_dicts,
            }

            self._json = json.dumps(
                data,
                separators=(',', ':'),  # Remove spaces from separators for more compact representation
                sort_keys=True,
            )
        return self._json

    @classmethod
    def from_json(cls, blockrecord_json):
        """
        Return a BlockRecordSet from a json list.
        """
        data = json.loads(blockrecord_json)
        course_key = data['course_key']
        if course_key is not None:
            course_key = CourseKey.from_string(course_key)
        else:
            # If there was no course key, there are no blocks.
            assert len(data['blocks']) == 0
        block_dicts = data['blocks']
        record_generator = (
            BlockRecord(
                locator=UsageKey.from_string(block["locator"]).replace(course_key=course_key),
                weight=block["weight"],
                max_score=block["max_score"],
            )
            for block in block_dicts
        )
        return cls(record_generator)

    def to_hash(self):
        """
        Return a hashed version of the list of block records.

        This currently hashes using sha1, and returns a base64 encoded version
        of the binary digest.  In the future, different algorithms could be
        supported by adding a label indicated which algorithm was used, e.g.,
        "sha256$j0NDRmSPa5bfid2pAcUXaxCm2Dlh3TwayItZstwyeqQ=".
        """
        if self._hash is None:
            self._hash = b64encode(sha1(self.to_json()).digest())
        return self._hash


class VisibleBlocksQuerySet(models.QuerySet):
    """
    A custom QuerySet representing VisibleBlocks.
    """

    def create_from_blockrecords(self, blocks):
        """
        Creates a new VisibleBlocks model object.

        Argument 'blocks' should be a BlockRecordSet.
        """

        if not isinstance(blocks, BlockRecordSet):
            blocks = BlockRecordSet(blocks)

        model, _ = self.get_or_create(hashed=blocks.to_hash(), defaults={'blocks_json': blocks.to_json()})
        return model

    def hash_from_blockrecords(self, blocks):
        """
        Return the hash for a given BlockRecordSet, serializing the records if
        possible, but returning the hash even if an IntegrityError occurs.
        """

        if not isinstance(blocks, BlockRecordSet):
            blocks = BlockRecordSet(blocks)

        try:
            with transaction.atomic():
                model = self.create_from_blockrecords(blocks)
        except IntegrityError:
            # If an integrity error occurs, the VisibleBlocks model we want to
            # create already exists.  The hash is still the correct value.
            return blocks.to_hash()
        else:
            # No error occurred
            return model.hashed


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

    objects = VisibleBlocksQuerySet.as_manager()

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
        return BlockRecordSet.from_json(self.blocks_json)


class PersistentSubsectionGradeQuerySet(models.QuerySet):
    """
    A custom QuerySet, that handles creating a VisibleBlocks model on creation, and
    extracts the course id from the provided usage_key.
    """
    def create(self, **kwargs):
        """
        Instantiates a new model instance after creating a VisibleBlocks instance.

        Arguments:
            user_id (int)
            usage_key (serialized UsageKey)
            course_version (str)
            subtree_edited_timestamp (datetime)
            earned_all (float)
            possible_all (float)
            earned_graded (float)
            possible_graded (float)
            visible_blocks (iterable of BlockRecord)
        """
        visible_blocks = kwargs.pop('visible_blocks')
        kwargs['course_version'] = kwargs.get('course_version', None) or ""
        if not kwargs.get('course_id', None):
            kwargs['course_id'] = kwargs['usage_key'].course_key

        visible_blocks_hash = VisibleBlocks.objects.hash_from_blockrecords(blocks=visible_blocks)
        return super(PersistentSubsectionGradeQuerySet, self).create(
            visible_blocks_id=visible_blocks_hash,
            **kwargs
        )


class PersistentSubsectionGrade(TimeStampedModel):
    """
    A django model tracking persistent grades at the subsection level.
    """

    class Meta(object):
        unique_together = [
            # * Specific grades can be pulled using all three columns,
            # * Progress page can pull all grades for a given (course_id, user_id)
            # * Course staff can see all grades for a course using (course_id,)
            ('course_id', 'user_id', 'usage_key'),
        ]

    # primary key will need to be large for this table
    id = UnsignedBigIntAutoField(primary_key=True)  # pylint: disable=invalid-name

    # uniquely identify this particular grade object
    user_id = models.IntegerField(blank=False)
    course_id = CourseKeyField(blank=False, max_length=255)
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

    # track which blocks were visible at the time of grade calculation
    visible_blocks = models.ForeignKey(VisibleBlocks, db_column='visible_blocks_hash', to_field='hashed')

    # use custom manager
    objects = PersistentSubsectionGradeQuerySet.as_manager()

    def __unicode__(self):
        """
        Returns a string representation of this model.
        """
        return u"{} user: {}, course version: {}, subsection {} ({}). {}/{} graded, {}/{} all".format(
            type(self).__name__,
            self.user_id,
            self.course_version,
            self.usage_key,
            self.visible_blocks_id,
            self.earned_graded,
            self.possible_graded,
            self.earned_all,
            self.possible_all,
        )

    @classmethod
    def save_grade(cls, **kwargs):
        """
        Wrapper for create_grade or update_grade, depending on which applies.
        Takes the same arguments as both of those methods.
        """
        user_id = kwargs.pop('user_id')
        usage_key = kwargs.pop('usage_key')

        try:
            with transaction.atomic():
                grade, is_created = cls.objects.get_or_create(
                    user_id=user_id,
                    course_id=usage_key.course_key,
                    usage_key=usage_key,
                    defaults=kwargs,
                )
                log.info(u"Persistent Grades: Grade model saved: {0}".format(grade))
        except IntegrityError:
            cls.update_grade(user_id=user_id, usage_key=usage_key, **kwargs)
            log.warning(
                u"Persistent Grades: Integrity error trying to save grade for user: {0}, usage key: {1}, defaults: {2}"
                .format(
                    user_id,
                    usage_key,
                    **kwargs
                )
            )
        else:
            if not is_created:
                grade.update(**kwargs)

    @classmethod
    def read_grade(cls, user_id, usage_key):
        """
        Reads a grade from database

        Arguments:
            user_id: The user associated with the desired grade
            usage_key: The location of the subsection associated with the desired grade

        Raises PersistentSubsectionGrade.DoesNotExist if applicable
        """
        return cls.objects.get(
            user_id=user_id,
            course_id=usage_key.course_key,  # course_id is included to take advantage of db indexes
            usage_key=usage_key,
        )

    @classmethod
    def update_grade(
            cls,
            user_id,
            usage_key,
            course_version,
            subtree_edited_timestamp,
            earned_all,
            possible_all,
            earned_graded,
            possible_graded,
            visible_blocks,
    ):
        """
        Updates a previously existing grade.

        This is distinct from update() in that `grade.update()` operates on an
        existing grade object, while this is a classmethod that pulls the grade
        from the database, and then updates it.  If you already have a grade
        object, use the update() method on that object to avoid an extra
        round-trip to the database.  Use this classmethod if all you have are a
        user and the usage key of an existing grade.

        Requires all the arguments listed in docstring for create_grade
        """
        grade = cls.read_grade(
            user_id=user_id,
            usage_key=usage_key,
        )

        grade.update(
            course_version=course_version,
            subtree_edited_timestamp=subtree_edited_timestamp,
            earned_all=earned_all,
            possible_all=possible_all,
            earned_graded=earned_graded,
            possible_graded=possible_graded,
            visible_blocks=visible_blocks,
        )

    def update(
            self,
            course_version,
            subtree_edited_timestamp,
            earned_all,
            possible_all,
            earned_graded,
            possible_graded,
            visible_blocks,
    ):
        """
        Modify an existing PersistentSubsectionGrade object, saving the new
        version.
        """
        visible_blocks_hash = VisibleBlocks.objects.hash_from_blockrecords(blocks=visible_blocks)

        self.course_version = course_version or ""
        self.subtree_edited_timestamp = subtree_edited_timestamp
        self.earned_all = earned_all
        self.possible_all = possible_all
        self.earned_graded = earned_graded
        self.possible_graded = possible_graded
        self.visible_blocks_id = visible_blocks_hash  # pylint: disable=attribute-defined-outside-init
        self.save()
        log.info(u"Persistent Grades: Grade model updated: {0}".format(self))
