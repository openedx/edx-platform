"""
Test the interaction with the learning_sequences app, where course outlines are
stored.
"""
from datetime import datetime, timezone

from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.learning_sequences.data import (
    CourseOutlineData,
    ExamData,
    VisibilityData,
)
from openedx.core.djangoapps.content.learning_sequences.api import get_course_outline
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..outlines import CourseStructureError, get_outline_from_modulestore


class OutlineFromModuleStoreTestCase(ModuleStoreTestCase):
    """
    These tests all set up some sort of course content data in the modulestore
    and extract that data using get_course_outline() to make sure that it
    creates the CourseOutlineData that we expect.

    The learning_sequences app has its own tests to test different scenarios for
    creating the outline. This set of tests only cares about making sure the
    data comes out of the Modulestore in the way we expect.

    Comparisons are done on individual attributes rather than making a complete
    CourseOutline object for comparison, so that more data fields can be added
    later without breaking tests.
    """
    ENABLED_SIGNALS = []
    ENABLED_CACHES = []

    def setUp(self):
        super().setUp()

        self.course_key = CourseKey.from_string("course-v1:TNL+7733+OutlineFromModuleStoreTestCase")

        # This CourseFactory will be a reference to data in the *draft* branch.
        # Creating this does "auto-publish" – all container types changes do,
        # and everything we care about for outlines is a container (section,
        # sequence, unit). But publish version/time metadata will not match the
        # published branch.
        self.draft_course = CourseFactory.create(
            org=self.course_key.org,
            course=self.course_key.course,
            run=self.course_key.run,
            default_store=ModuleStoreEnum.Type.split,
            display_name="OutlineFromModuleStoreTestCase Course",
        )

    def test_empty_course_metadata(self):
        """Courses start empty, and could have a section with no sequences."""
        # The learning_sequences app only uses the published branch, which will
        # have slightly different metadata for version and published_at (because
        # it's created a tiny fraction of a second later). Explicitly pull from
        # published branch to make sure we have the right data.
        with self.store.branch_setting(ModuleStoreEnum.Branch.published_only, self.course_key):
            published_course = self.store.get_course(self.course_key, depth=2)
        outline = get_outline_from_modulestore(self.course_key)

        # Check basic metdata...
        assert outline.title == "OutlineFromModuleStoreTestCase Course"

        # published_at
        assert isinstance(outline.published_at, datetime)
        assert outline.published_at == published_course.subtree_edited_on
        assert outline.published_at.tzinfo == timezone.utc

        # published_version
        assert isinstance(outline.published_version, str)
        assert outline.published_version == str(published_course.course_version)  # str, not BSON

        # Misc.
        assert outline.entrance_exam_id == published_course.entrance_exam_id
        assert outline.days_early_for_beta == published_course.days_early_for_beta
        assert outline.self_paced == published_course.self_paced

        # Outline stores an enum for course_visibility, while Modulestore uses strs...
        assert outline.course_visibility.value == published_course.course_visibility

        # Check that the contents are empty.
        assert len(outline.sections) == 0
        assert len(outline.sequences) == 0

    def test_normal_sequence(self):
        ms_seq = self._create_seq_in_new_section(display_name="Normal Sequence")
        outline_seq, usage_key = self._outline_seq_data(ms_seq)
        assert outline_seq.usage_key == usage_key
        assert outline_seq.title == "Normal Sequence"
        assert outline_seq.visibility == VisibilityData()
        assert outline_seq.exam == ExamData()
        assert outline_seq.inaccessible_after_due is False

    def test_hidden_after_due_sequence(self):
        ms_seq = self._create_seq_in_new_section(hide_after_due=True)
        outline_seq, _usage_key = self._outline_seq_data(ms_seq)
        assert outline_seq.inaccessible_after_due is True

    def test_staff_only_seq(self):
        ms_seq = self._create_seq_in_new_section(visible_to_staff_only=True)
        outline_seq, _usage_key = self._outline_seq_data(ms_seq)
        assert outline_seq.visibility == VisibilityData(visible_to_staff_only=True)

    def test_hidden_from_toc_seq(self):
        ms_seq = self._create_seq_in_new_section(hide_from_toc=True)
        outline_seq, _usage_key = self._outline_seq_data(ms_seq)
        assert outline_seq.visibility == VisibilityData(hide_from_toc=True)

    def test_practice_exam_seq(self):
        ms_seq = self._create_seq_in_new_section(
            is_time_limited=True,
            is_practice_exam=True,
            is_proctored_enabled=True,
        )
        outline_seq, _usage_key = self._outline_seq_data(ms_seq)
        assert outline_seq.exam == ExamData(
            is_time_limited=True,
            is_practice_exam=True,
            is_proctored_enabled=True,
        )

    def test_proctored_exam_seq(self):
        ms_seq = self._create_seq_in_new_section(
            is_time_limited=True,
            is_proctored_enabled=True,
        )
        outline_seq, _usage_key = self._outline_seq_data(ms_seq)
        assert outline_seq.exam == ExamData(
            is_time_limited=True,
            is_proctored_enabled=True,
        )

    def test_multiple_sections(self):
        """Make sure sequences go into the right places."""
        with self.store.bulk_operations(self.course_key):
            section_1 = ItemFactory.create(
                parent_location=self.draft_course.location,
                category='chapter',
                display_name="Section 1 - Three Sequences",
            )
            ItemFactory.create(
                parent_location=self.draft_course.location,
                category='chapter',
                display_name="Section 2 - Empty",
            )
            for i in range(3):
                ItemFactory.create(
                    parent_location=section_1.location,
                    category='sequential',
                    display_name=f"Seq_1_{i}",
                )

        outline = get_outline_from_modulestore(self.course_key)

        assert len(outline.sections) == 2
        assert len(outline.sections[0].sequences) == 3
        assert outline.sections[0].sequences[0].title == "Seq_1_0"
        assert outline.sections[0].sequences[1].title == "Seq_1_1"
        assert outline.sections[0].sequences[2].title == "Seq_1_2"
        assert len(outline.sections[1].sequences) == 0

    def test_unit_in_section(self):
        """
        Test when the structure is Course -> Section -> Unit.

        Studio disallows this, but it's possible to craft in OLX. This type of
        structure is unsupported. We should fail with a CourseStructureError, as
        that will emit useful debug information.
        """
        # Course -> Section -> Unit (No Sequence)
        with self.store.bulk_operations(self.course_key):
            section = ItemFactory.create(
                parent_location=self.draft_course.location,
                category='chapter',
                display_name="Section",
            )
            ItemFactory.create(
                parent_location=section.location,
                category='vertical',
                display_name="Unit"
            )

        with self.assertRaises(CourseStructureError):
            get_outline_from_modulestore(self.course_key)

    def test_sequence_without_section(self):
        """
        Test when the structure is Course -> Sequence -> Unit.

        Studio disallows this, but it's possible to craft in OLX. This type of
        structure is unsupported. We should fail with a CourseStructureError, as
        that will emit useful debug information.
        """
        # Course -> Sequence (No Section)
        with self.store.bulk_operations(self.course_key):
            seq = ItemFactory.create(
                parent_location=self.draft_course.location,
                category='sequential',
                display_name="Sequence",
            )
            ItemFactory.create(
                parent_location=seq.location,
                category='vertical',
                display_name="Unit",
            )

        with self.assertRaises(CourseStructureError):
            get_outline_from_modulestore(self.course_key)

    def _outline_seq_data(self, modulestore_seq):
        """
        (CourseLearningSequenceData, UsageKey) for a Modulestore sequence.

        When we return the UsageKey part of the tuple, we'll strip out any
        CourseKey branch information that might be present (the most recently
        published set of blocks will have version information when they're
        published, but learning_sequences ignores all of that).
        """
        outline = get_outline_from_modulestore(self.course_key)

        # Recently modified content can have full version information on their
        # CourseKeys. We need to strip that out and have versionless-CourseKeys
        # or they won't be found properly.
        versionless_usage_key = modulestore_seq.location.map_into_course(self.course_key)
        outline_seq_data = outline.sequences[versionless_usage_key]

        return outline_seq_data, versionless_usage_key

    def _create_seq_in_new_section(self, **kwargs):
        """
        Helper that creates a sequence in a new section and returns it.

        Just reduces the boilerplate of "make me a sequence with the following
        params in a new section/chapter so I can do asserts on how it translated
        over."
        """
        with self.store.bulk_operations(self.course_key):
            section = ItemFactory.create(
                parent_location=self.draft_course.location,
                category='chapter',
                display_name="Generated Section",
            )
            sequence = ItemFactory.create(
                parent_location=section.location,
                category='sequential',
                **kwargs,
            )

        return sequence


class OutlineFromModuleStoreTaskTestCase(ModuleStoreTestCase):
    """
    Test to make sure that the outline is created after course publishing. (i.e.
    that it correctly receives the course_published signal).
    """
    ENABLED_SIGNALS = ['course_published']

    def test_task_invocation(self):
        """Test outline auto-creation after course publish"""
        course_key = CourseKey.from_string("course-v1:TNL+7733+2021-01-21")
        with self.assertRaises(CourseOutlineData.DoesNotExist):
            get_course_outline(course_key)

        course = CourseFactory.create(
            org=course_key.org,
            course=course_key.course,
            run=course_key.run,
            default_store=ModuleStoreEnum.Type.split,
        )
        section = ItemFactory.create(
            parent_location=course.location,
            category="chapter",
            display_name="First Section"
        )
        ItemFactory.create(
            parent_location=section.location,
            category="sequential",
            display_name="First Sequence"
        )
        ItemFactory.create(
            parent_location=section.location,
            category="sequential",
            display_name="Second Sequence"
        )
        self.store.publish(course.location, self.user.id)

        outline = get_course_outline(course_key)
        assert len(outline.sections) == 1
        assert len(outline.sequences) == 2
