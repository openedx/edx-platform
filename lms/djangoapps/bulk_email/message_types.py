"""
ACE message types for bulk course emails.
"""

from openedx.core.djangoapps.ace_common.message import BaseMessageType


class BulkEmail(BaseMessageType):
    """
    Course message to list of recepient by instructors.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options['from_address'] = kwargs['context']['from_address']
<<<<<<< HEAD
=======
        self.options['transactional'] = True
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
