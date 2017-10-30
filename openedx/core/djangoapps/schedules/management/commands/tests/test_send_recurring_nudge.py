from unittest import skipUnless

from django.conf import settings

from openedx.core.djangoapps.schedules import tasks
from openedx.core.djangoapps.schedules.management.commands import send_recurring_nudge as nudge
from openedx.core.djangoapps.schedules.management.commands.tests.send_email_base import ScheduleSendEmailTestBase
from openedx.core.djangoapps.schedules.management.commands.tests.upsell_base import ScheduleUpsellTestMixin
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
@skipUnless(
    'openedx.core.djangoapps.schedules.apps.SchedulesConfig' in settings.INSTALLED_APPS,
    "Can't test schedules if the app isn't installed",
)
class TestSendRecurringNudge(ScheduleUpsellTestMixin, ScheduleSendEmailTestBase):
    __test__ = True

    # pylint: disable=protected-access
    tested_task = tasks.ScheduleRecurringNudge
    deliver_task = tasks._recurring_nudge_schedule_send
    tested_command = nudge.Command
    deliver_config = 'deliver_recurring_nudge'
    enqueue_config = 'enqueue_recurring_nudge'
    expected_offsets = (-3, -10)
