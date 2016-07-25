"""
Models used for robust grading.

Robust grading allows student scores to be saved per-subsection independent
of any changes that may occur to the course after the score is achieved.
"""

from django.db import models
from model_utils.models import TimeStampedModel

from coursewarehistoryextended.fields import UnsignedBigIntAutoField
from opaque_keys.edx.locator import BlockUsageLocator
from xmodule_django.models import CourseKeyField, UsageKeyField

from hashlib import md5
import json


class VisibleBlocks(models.Model):
    """
    A django model used to track the state of a set of visible blocks under a given subsection at the time they are
    used for grade calculation.

    This state is represented using an array of serialized BlockRecords, stored in the blocks_json field. A
    hash of this json array is used for lookup purposes.
    """
    _blocks_json = models.TextField(db_column="blocks_json")
    hashed = models.CharField(max_length=32, primary_key=True)

    def __unicode__(self):
        """
        String representation of this model.
        """
        return self.hashed

    @classmethod
    def create(cls, blocks):
        """
        Creates a new VisibleBlocks model. Argument 'blocks' should be an array of BlockRecords.
        """
        # Start by sorting the blocks to ensure equality regardless of how the blocks are ordered
        sorted_blocks = sorted(
            blocks,
            key=lambda block: '{}{}{}'.format(block.block_key, block.max_score, block.weight)
        )
        _blocks_json = json.dumps(
            [
                block.to_dict()
                for block in sorted_blocks
            ]
        )
        hashed = md5(_blocks_json).hexdigest()
        model, _ = cls.objects.get_or_create(hashed=hashed, defaults={'_blocks_json': _blocks_json})
        return model

    @property
    def blocks(self):
        """
        Returns the blocks_json data stored on this model as an array of BlockRecords. If for some reason block_json
        is not parsable, the json error will bubble up.
        """
        block_dicts = json.loads(self._blocks_json)
        return [
            BlockRecord(data['weight'], data['max_score'], data['block_key'])
            for data in block_dicts
        ]

    @blocks.setter
    def blocks(self, value):
        """
        Not implemented, as VisibleBlocks instances are intended to be write-once and not change after creation.
        """
        raise NotImplementedError(
            "Property 'blocks' cannot be modified on an existing VisibleBlocks model. Create a new instance."
        )


class BlockRecord(object):
    """
    An object encapsulating all relevant information for representing a block at the time it was used for grade
    calculation.
    """

    def __init__(self, weight, max_score, locator):
        """
        Creates a BlockRecord.

        Params:
            weight (float)
            max_score (float)
            locator (BlockUsageLocator or string)
        """
        self.weight = weight
        self.max_score = max_score
        # pylint: disable=protected-access
        self.block_key = locator._to_string() if isinstance(locator, BlockUsageLocator) else locator

    def to_dict(self):
        """
        Serialize this object to a dict object.
        """
        return {
            'weight': self.weight,
            'max_score': self.max_score,
            'block_key': self.block_key,
        }

    @property
    def locator(self):
        """
        Convenience property allowing a BlockUsageLocator to be returned from this object's serialized data.
        """
        return BlockUsageLocator._from_string(self.block_key)  # pylint: disable=protected-access


class PersistentSubsectionGrade(TimeStampedModel):
    """
    A django model tracking persistent grades at the subsection level.

    TODO: here are the other query patterns listed in the ticket that are not currently used. Should any of these
    indices be built?
        user_id, course_id, content_type, is_valid
        course_id, edit-timestamp
        edit-timestamp
    """

    class Meta(object):
        index_together = [
            ('user_id', 'usage_key')
        ]

        unique_together = (('user_id', 'usage_key'))

    id = UnsignedBigIntAutoField(primary_key=True)  # pylint: disable=invalid-name
    subtree_edited_date = models.DateTimeField('last content edit timestamp')
    user_id = models.CharField(max_length=255)
    earned_all = models.IntegerField()
    possible_all = models.IntegerField()
    earned_graded = models.IntegerField()
    possible_graded = models.IntegerField()

    course_id = CourseKeyField(max_length=255)
    usage_key = UsageKeyField(max_length=255)
    course_version = models.CharField('guid of latest course version', max_length=255)

    #is_valid = models.BinaryField()  # Might be needed if doing async updates

    visible_blocks = models.ForeignKey(VisibleBlocks)

    def __unicode__(self):
        """
        Returns a string representation of this model.
        """
        return "PersistentSubsectionGrade for user {} in subsection {}".format(self.user_id, self.usage_key)

    @classmethod
    def save_grade(cls, **kwargs):
        """
        Wrapper for create_grade or update_grade, depending on which applies.
        Takes the same arguments as both of thsoe methods.
        """
        try:
            cls.update(**kwargs)
        except cls.DoesNotExist:
            cls.create(**kwargs)

    @classmethod
    def create(cls, **kwargs):
        """
        Instantiates a new model instance using the provided kwargs, formatted as follows:
            user_id: "student12345"
            usage_key: "block-v1:edX+BeAwesomeX+2016+type@subsection+block@f007ba11"
            course_version: "deadbeef"
            subtree_edited_date: "2016-08-01 18:53:24.354741"
            earned_all: 6
            possible_all: 12
            earned_graded: 6
            possible_graded: 8
            visible_blocks: [<list of BlockRecord objects>]
        """
        visible_blocks_model = VisibleBlocks.create(blocks=kwargs['visible_blocks'])

        model = cls.objects.create(
            user_id=kwargs['user_id'],
            course_id=kwargs['usage_key'].course_key,
            usage_key=kwargs['usage_key'],
            course_version=kwargs['course_version'],
            subtree_edited_date=kwargs['subtree_edited_date'],
            earned_all=kwargs['earned_all'],
            possible_all=kwargs['possible_all'],
            earned_graded=kwargs['earned_graded'],
            possible_graded=kwargs['possible_graded'],
            visible_blocks=visible_blocks_model,
        )
        return model

    @classmethod
    def read(cls, **kwargs):
        """
        Reads a grade from database

        Arguments:
            user_id: The user associated with the desired grade
            usage_key: The location of the subsection associated with the desired grade

        Raises PersistentSubsectionGrade.DoesNotExist if applicable
        """
        return cls.objects.get(
            user_id=kwargs["user_id"],
            usage_key=kwargs["usage_key"],
        )

    @classmethod
    def update(cls, **kwargs):
        """
        Updates a previously existing grade.

        Requires all the arguments listed in docstring for create_grade
        """
        grade = cls.objects.get(
            user_id=kwargs["user_id"],
            usage_key=kwargs["usage_key"],
        )

        visible_blocks_model = VisibleBlocks.create(blocks=kwargs['visible_blocks'])

        grade.course_version = kwargs["course_version"]
        grade.subtree_edited_date = kwargs["subtree_edited_date"]
        grade.earned_all = kwargs["earned_all"]
        grade.possible_all = kwargs["possible_all"]
        grade.earned_graded = kwargs["earned_graded"]
        grade.possible_graded = kwargs["possible_graded"]
        grade.visible_blocks = visible_blocks_model
        grade.save()
