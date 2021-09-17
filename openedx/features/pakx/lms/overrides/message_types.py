"""
ACE message types for Course progress emails.
"""


from openedx.core.djangoapps.ace_common.message import BaseMessageType


class CourseProgress(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(CourseProgress, self).__init__(*args, **kwargs)

        self.options['transactional'] = True


class ContactUs(BaseMessageType):
    def __init__(self, *args, **kwargs):
        super(ContactUs, self).__init__(*args, **kwargs)

        self.options['transactional'] = True
