from django.db import models
from model_utils.models import TimeStampedModel

from coursewarehistoryextended.fields import UnsignedBigIntAutoField
from xmodule_django.models import BlockTypeKeyField, CourseKeyField

import json


class VisibleBlocksModel(models.Model):
    """
    A django model used to track the state of a set of visibile blocks under a given subsection at the time they are
    used for grade calculation.

    This state is represented using an array of serialized BlockRecords, stored in the blocks_json field. A
    hash of this json array is used for lookup purposes.

    Note that while blocks_json may be accessed directly (this is python, we're all consenting adults here), the
    blocks property is provided to make deserialization more convenient. Similarly, hashed should not be set directly.
    """
    blocks_json = models.TextField()
    hashed = models.CharField(max_length=255, primary_key=True)

    def __init__(self, *args, **kwargs):
        """
        Creates a new VisibleBlocksModel. Keyword argument 'blocks' should be an array of BlockRecords. KeyError will
        be raised if this argument is not present.
        """
        blocks = kwargs.pop('blocks')
        super(VisibleBlocksModel, self).__init__(*args, **kwargs)
        self.blocks_json = json.dumps(
            [
                block.to_json()
                for block in blocks
            ]
        )
        self.hashed = hash(self.blocks_json)  # TODO: better hash algo here?

    @property
    def blocks(self):
        """
        Returns the blocks_json data stored on this model as an array of BlockRecords. If for some reason block_json
        is not parsable, the json error will bubble up.
        """
        block_dicts = json.loads(self.blocks_json)
        return [BlockRecord(data) for data in block_dicts]

    @blocks.setter
    def blocks(self, value):
        """
        Not implemented, as VisibleBlocks instances are intended to be write-once and not change after creation.
        """
        raise NotImplementedError(
            "Property 'blocks' cannot be modified on an existing VisibleBlocksModel. Create a new instance."
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

        unique_together = (('user_id', 'course_id', 'block_type', 'block_id'))

    id = UnsignedBigIntAutoField(primary_key=True)  # pylint: disable=invalid-name
    subtree_edited_date = models.DateTimeField('last content edit timestamp')
    user_id = models.CharField(max_length=255)
    earned_all = models.IntegerField()
    possible_all = models.IntegerField()
    earned_graded = models.IntegerField()
    possible_graded = models.IntegerField()

    # TODO: Make sure this matches up w/ what Nimisha's exposing in her PR
    course_version = models.CharField('guid of latest course version', max_length=255)

    # These 3 are essentially a deconstructed UsageKey
    course_id = CourseKeyField(max_length=255)
    block_type = BlockTypeKeyField(max_length=255)
    block_id = models.CharField(max_length=255)  # TODO: CharField correct here?

    #is_valid = models.BinaryField()  # Might be needed if doing async updates

    visible_blocks = models.ForeignKey(VisibleBlocksModel)

    @classmethod
    def create_grade(cls, **kwargs):
        """
        Instantiates a new model instance using the provided kwargs, formatted as follows:

        TODO: document the expected dict fully once it's finalized
        """
        # TODO: do some validation of kwargs here, ensure required args are present

        # another TODO: figure out how to split a blockkey nicely
        block_id, block_type, course_id = kwargs['block_key'].split(magic_params='???')  # block_key is required

        # one other TODO: do we require visible_blocks to be precalculated and passed in here, or can we calculate them given the block_key and user_id?
        # just using a hard-coded sample for now until ^ is resolved
        visible_blocks = [BlockRecord({'weight': 0, 'max_score': 0, 'id': 'lol_idk?12345!'})]
        visible_blocks_model = VisibleBlocksModel.objects.create(blocks=visible_blocks)

        model = cls.objects.create(
            user_id=kwargs['user_id'],  # required
            course_id=course_id,
            block_type=block_type,
            block_id=block_id,
            subtree_edited_date=kwargs['subtree_edited_date'],  # required? or can we use "now" as a default?
            earned_all=kwargs['earned_all'],  # required, specify 0 if needed
            possible_all=kwargs['possible_all'],  # required, specify 0 if needed
            earned_graded=kwargs['earned_graded'],  # required, specify 0 if needed
            possible_graded=kwargs['possible_graded'],  # required, specify 0 if needed
            course_version=kwargs['course_version'],  # required
            visible_blocks=visible_blocks_model,  # maybe required? see TODO above
        )
        return model

    @classmethod
    def read_grade(cls, **kwargs):
        """
        Reads a grade from database

        TODO: define arg list
        """
        pass

    @classmethod
    def update_grade(cls, **kwargs):
        """
        Updates a previously existing grade.

        TODO: define arg list
        TODO: should this create a model if none already exists? or fail and require the caller to call create_grade?
        """
        pass

    # TODO: we have Create, Read, and Update methods; is Delete needed as well, or does that violate the "persistance" we're going for?


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
