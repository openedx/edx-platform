from django.db import models
from model_utils.models import TimeStampedModel

from coursewarehistoryextended.fields import UnsignedBigIntAutoField
from xmodule_django.models import CourseKeyField, UsageKeyField

from hashlib import md5
import json


class VisibleBlocksModel(models.Model):
    """
    A django model used to track the state of a set of visible blocks under a given subsection at the time they are
    used for grade calculation.

    This state is represented using an array of serialized BlockRecords, stored in the blocks_json field. A
    hash of this json array is used for lookup purposes.
    """
    _blocks_json = models.TextField(db_column="blocks_json")
    hashed = models.CharField(max_length=32, primary_key=True)

    def __init__(self, *args, **kwargs):
        """
        Creates a new VisibleBlocksModel. Keyword argument 'blocks' should be an array of BlockRecords. KeyError will
        be raised if this argument is not present.
        """
        blocks = kwargs.pop('blocks')
        super(VisibleBlocksModel, self).__init__(*args, **kwargs)
        self._blocks_json = json.dumps(
            [
                block.to_json()
                for block in blocks
            ]
        )
        self.hashed = md5(self._blocks_json).hexdigest()

    @property
    def blocks(self):
        """
        Returns the blocks_json data stored on this model as an array of BlockRecords. If for some reason block_json
        is not parsable, the json error will bubble up.
        """
        block_dicts = json.loads(self._blocks_json)
        return [BlockRecord(data) for data in block_dicts]

    @blocks.setter
    def blocks(self, value):
        """
        Not implemented, as VisibleBlocks instances are intended to be write-once and not change after creation.
        """
        raise NotImplementedError(
            "Property 'blocks' cannot be modified on an existing VisibleBlocksModel. Create a new instance."
        )


class BlockRecord(object):
    weight = None
    max_score = None
    id = None

    def __init__(self, value_dict):
        """
        Deserialize a dictionary into this object.
        """
        self.weight = value_dict['weight']
        self.max_score = value_dict['max_score']
        self.id = value_dict['id']

    def to_json(self):
        """
        Serialize this object to json.
        """
        return json.dumps(
            {
                'weight': self.weight,
                'max_score': self.max_score,
                'id': self.id,
            }
        )


class PersistentSubsectionGradeModel(TimeStampedModel):
    """
    A django model tracking persistent grades at the subsection level.

    TODO: intended query patterns are fluid at the moment, document them here as they're firmed up.
    """

    class Meta(object):
        index_together = [
            # TODO: nail down indices as we flesh out the API layer
        ]

        # TODO: should course_version be included here?
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

    visible_blocks = models.ForeignKey(VisibleBlocksModel)

    @classmethod
    def create_grade(cls, **kwargs):
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
            visible_blocks: [<list of BlockRecord objects>] <--- this is still up for debate
        """
        # TODO: do we require visible_blocks to be precalculated and passed in here, or can we calculate them given the block_key and user_id?
        visible_blocks = [  # using a hard-coded sample until ^ is resolved
            BlockRecord(
                {
                    'weight': 0,
                    'max_score': 0,
                    'id': 'lol_idk?12345!'
                }
            )
        ]
        visible_blocks_model = VisibleBlocksModel.objects.get_or_create(blocks=visible_blocks)

        model = cls.objects.create(
            user_id=kwargs['user_id'],
            course_id=kwargs['usage_key'].course_key(),
            usage_key=kwargs['usage_key']
            course_version=kwargs['course_version'],
            subtree_edited_date=kwargs['subtree_edited_date'],  # TODO: required, or default to now?
            earned_all=kwargs['earned_all'],
            possible_all=kwargs['possible_all'],
            earned_graded=kwargs['earned_graded'],
            possible_graded=kwargs['possible_graded'],
            visible_blocks=visible_blocks_model,
        )
        return model

    @classmethod
    def read_grade(cls, **kwargs):
        """
        Reads a grade from database

        Arguments:
            user_id: The user associated with the desired grade
            usage_key: The location of the subsection associated with the desired grade

        Raises PersistentSubsectionGradeModel.DoesNotExist if applicable
        """
        return cls.objects.get(
            user_id=kwargs["user_id"],
            usage_key=kwargs["usage_key"],
        )

    @classmethod
    def update_grade(cls, **kwargs):
        """
        Updates a previously existing grade.

        Requires all the arguments listed in docstring for create_grade
        """
        grade = cls.objects.get(
            user_id=kwargs["user_id"],
            usage_key=kwargs["usage_key"],
        )
        grade.course_version=kwargs["course_version"]
        grade.subtree_edited_date=kwargs["subtree_edited_date"]
        grade.earned_all=kwargs["earned_all"]
        grade.possible_all=kwargs["possible_all"]
        grade.earned_graded=kwargs["earned_graded"]
        grade.possible_graded=kwargs["possible_graded"]
        grade.visible_blocks=kwargs["visible_blocks"]
        grade.save()
