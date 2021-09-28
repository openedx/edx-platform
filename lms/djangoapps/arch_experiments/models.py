from django.db import models
from lms.djangoapps.courseware.fields import UnsignedBigIntAutoField
from model_utils.models import TimeStampedModel


class BrokerOutboxMessage(TimeStampedModel):
    """
    How to use the outbox:

    Wherever you want to send a message to a topic, create and save an outbox message object:

    ```
    BrokerOutboxMessage(serialized_key, serialized_value, topic_name).save()
    ```

    Do this within the transaction that persists this data to any relevant sources of truth(sql tables). That way you'll
    only send the message if the database transaction succeeded.
    """
    # primary key will need to be large for this table
    # Do we want a UUID instead?  Will that make it more performant when we want
    # to horizontally scale producer management command.
    id = UnsignedBigIntAutoField(primary_key=True)  # pylint: disable=invalid-name

    # TODO: Need a max_length so that we can fail early on this?
    # https://django-mysql.readthedocs.io/en/latest/model_fields/resizable_text_binary_fields.html
    serialized_key = models.BinaryField()
    serialized_value = models.BinaryField()

    # Should this be a CharField with a max length?
    topic_name = models.TextField()
