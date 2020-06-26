import logging
from collections import defaultdict, OrderedDict
from datetime import datetime

from django.contrib.auth import get_user_model
from edx_when.api import get_dates_for_course
from opaque_keys.edx.keys import CourseKey, UsageKey

from ..data import ScheduleData, ScheduleItemData, UserCourseOutlineData
from .base import OutlineProcessor

User = get_user_model()
log = logging.getLogger(__name__)


class ScheduleOutlineProcessor(OutlineProcessor):
    """
    Responsible for applying all start/due/end date outline processing.

    We never hide the existence of a piece of content because of start or due
    dates. Content may be inaccessible because it has yet to be released or the
    exam has closed, but students are never prevented from knowing the content
    exists based on the start and due date information.

    This processor depends on edx-when to get customized due date information
    for users and content.

    Things we don't handle yet:
    * Beta test users
    * Self-paced courses
    * Things that are made inaccessible after they're due.
    """

    def __init__(self, course_key: CourseKey, user: User, at_time: datetime):
        super().__init__(course_key, user, at_time)
        self.dates = None
        self.keys_to_schedule_fields = defaultdict(dict)
        self._course_start = None
        self._course_end = None

    def load_data(self):
        """Pull dates information from edx-when."""
        # (usage_key, 'due'): datetime.datetime(2019, 12, 11, 15, 0, tzinfo=<UTC>)
        # TODO: Merge https://github.com/edx/edx-when/pull/48 and add `outline_only=True`
        self.dates = get_dates_for_course(self.course_key, self.user)

        for (usage_key, field_name), date in self.dates.items():
            self.keys_to_schedule_fields[usage_key][field_name] = date

        course_usage_key = self.course_key.make_usage_key('course', 'course')
        self._course_start = self.keys_to_schedule_fields[course_usage_key].get('start')
        self._course_end = self.keys_to_schedule_fields[course_usage_key].get('end')

    def inaccessible_sequences(self, full_course_outline):
        """
        This might include Sequences that have not yet started, or Sequences
        for exams that have closed. If a Section has not started, all of its
        Sequences are inaccessible, regardless of the individual Sequence start
        dates.
        """
        # If the course hasn't started at all, then everything is inaccessible.
        if self._course_start is None or self.at_time < self._course_start:
            return set(full_course_outline.sequences)

        inaccessible = set()
        for section in full_course_outline.sections:
            section_start = self.keys_to_schedule_fields[section.usage_key].get('start')
            if section_start and self.at_time < section_start:
                # If the section hasn't started yet, all the sequences it
                # contains are inaccessible, regardless of the start value for
                # those sequences.
                inaccessible |= {seq.usage_key for seq in section.sequences}
            else:
                for seq in section.sequences:
                    seq_start = self.keys_to_schedule_fields[seq.usage_key].get('start')
                    if seq_start and self.at_time < seq_start:
                        inaccessible.add(seq.usage_key)

        return inaccessible

    def schedule_data(self, pruned_course_outline: UserCourseOutlineData) -> ScheduleData:
        """
        Return supplementary scheduling information for this outline.

        Be careful to pass in a UserCourseOutlineData–i.e. an outline that has
        already been pruned to what a user is allowed to see. That way, we can
        use this to make sure that we're not returning data about
        LearningSequences that the user can't see because it was hidden by a
        different OutlineProcessor.
        """
        def _effective_start(*dates):
            specified_dates = [date for date in dates if date is not None]
            return max(specified_dates) if specified_dates else None

        pruned_section_keys = {section.usage_key for section in pruned_course_outline.sections}
        course_usage_key = self.course_key.make_usage_key('course', 'course')
        course_start = self.keys_to_schedule_fields[course_usage_key].get('start')
        course_end = self.keys_to_schedule_fields[course_usage_key].get('end')

        sequences = {}
        sections = {}
        for section in pruned_course_outline.sections:
            section_dict = self.keys_to_schedule_fields[section.usage_key]
            section_start = section_dict.get('start')
            section_effective_start = _effective_start(course_start, section_start)
            section_due = section_dict.get('due')

            sections[section.usage_key] = ScheduleItemData(
                usage_key=section.usage_key,
                start=section_start,
                effective_start=section_effective_start,
                due=section_due,
            )

            for seq in section.sequences:
                seq_dict = self.keys_to_schedule_fields[seq.usage_key]
                seq_start = seq_dict.get('start')
                seq_due = seq_dict.get('due')
                sequences[seq.usage_key] = ScheduleItemData(
                    usage_key=seq.usage_key,
                    start=seq_start,
                    effective_start=_effective_start(section_effective_start, seq_start),
                    due=seq_due,
                )

        return ScheduleData(
            course_start=course_start,
            course_end=course_end,
            sections=sections,
            sequences=sequences,
        )
