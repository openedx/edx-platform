
from edx_ace.policy import Policy, PolicyResult
from edx_ace.channel import ChannelType
from buil_email.models import Optout
from courseware.models import CourseScheduleConfiguration


class CourseEmailOptout(Policy):

    def check(self, message):
        course_id = message.context.get('course_id')
        if not course_id:
            return PolicyResult(deny=[])

        if Optout.objects.filter(user__username=message.recipient.username, course_id=course_id).exists():
            return PolicyResult(deny=[ChannelType.EMAIL])

        return PolicyResult(deny=[])


class CourseMessageEnabled(Policy):

    def check(self, message):
        course_id = message.context.get('course_id')
        if not course_id or message.app_label != 'schedules':
            return PolicyResult(deny=[])

        schedule_config = CourseScheduleConfiguration.current(course_id)
        if not schedule_config.enabled:
            return PolicyResult(deny=[ChannelType.ALL])

        if not schedule_config.recurring_reminder_message_enabled and message.name == 'recurringreminder':
            return PolicyResult(deny=[ChannelType.ALL])

        if not schedule_config.verified_upgrade_reminder_message_enabled and message.name == 'verifiedupgradedeadlinereminder':
            return PolicyResult(deny=[ChannelType.ALL])

        return PolicyResult(deny=[])
