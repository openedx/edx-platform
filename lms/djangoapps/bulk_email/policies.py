
from edx_ace.policy import Policy, PolicyResult
from edx_ace.channel import ChannelType
from opaque_keys.edx.keys import CourseKey

from bulk_email.models import Optout


class CourseEmailOptout(Policy):

    def check(self, message):
        course_id = message.context.get('course_id')
        if not course_id:
            return PolicyResult(deny=frozenset())

        course_key = CourseKey.from_string(course_id)
        if Optout.objects.filter(user__username=message.recipient.username, course_id=course_key).exists():
            return PolicyResult(deny={ChannelType.EMAIL})

        return PolicyResult(deny=frozenset())
