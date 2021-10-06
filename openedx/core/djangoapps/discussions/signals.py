"""
Signals for discussions
"""
from openedx_events.tooling import OpenEdxPublicSignal

from openedx.core.djangoapps.discussions.data import CourseDiscussionConfigurationData

# TODO: This will be moved to openedx_events. It's currently here to simplify the PR.
# .. event_type: org.openedx.learning.discussions.configuration.change.v1
# .. event_name: COURSE_DISCUSSIONS_UPDATED
# .. event_description: emitted when the configuration for a course's discussions changes in the course
# .. event_data: CourseDiscussionConfigurationData
COURSE_DISCUSSIONS_UPDATED = OpenEdxPublicSignal(
    event_type="org.openedx.learning.discussions.configuration.change.v1",
    data={
        "configuration": CourseDiscussionConfigurationData
    }
)
