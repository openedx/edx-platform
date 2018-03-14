"""
Test creation of aggregate completions when a user works through a course.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import timedelta
import logging

from completion.models import BlockCompletion
from completion.test_utils import CompletionWaffleTestMixin
from completion_aggregator.models import Aggregator
from django.utils import timezone
import pytest


from course_modes.models import CourseMode
from openedx.core.djangolib.testing.utils import skip_unless_lms
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.library_tools import LibraryToolsService
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import TEST_DATA_SPLIT_MODULESTORE, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, LibraryFactory
from xmodule.partitions.partitions import ENROLLMENT_TRACK_PARTITION_ID
from xmodule.partitions import partitions_service

log = logging.getLogger(__name__)


class _BaseTestCase(CompletionWaffleTestMixin, SharedModuleStoreTestCase):
    """
    Common functionality for Aggregator tests.
    """
    def setUp(self):
        super(_BaseTestCase, self).setUp()
        self.override_waffle_switch(True)
        self.user = UserFactory.create()

    def submit_completion_with_user(self, user, item, completion):
        return BlockCompletion.objects.submit_completion(
            user=user,
            course_key=self.course_key,
            block_key=item.location,
            completion=completion,
        )

    def submit_completion_for(self, item, completion):
        return self.submit_completion_with_user(self.user, item, completion)

    def aggregator_for(self, item, user=None):
        """
        Return the aggregator for the given item, or raise an Aggregator.DoesNotExist
        """
        qs = Aggregator.objects.all()
        if user:
            qs = qs.filter(user=user)
        return qs.get(block_key=item.location)

    def assert_expected_values(self, values_map, user=None):
        for item in values_map:
            if values_map[item]:
                agg = self.aggregator_for(item, user=user)
                self.assertEqual((agg.earned, agg.possible), values_map[item])
            else:
                with pytest.raises(Aggregator.DoesNotExist):
                    self.aggregator_for(item, user=user)


class DAGTestCase(_BaseTestCase):
    """
    Test that aggregators are created and updated properly for earned BlockCompletions.
    """

    @classmethod
    def setUpClass(cls):
        super(DAGTestCase, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.course_key = cls.course.id
        with cls.store.bulk_operations(cls.course.id):
            cls.chapter = ItemFactory.create(
                parent=cls.course,
                category="chapter",
            )
            cls.sequential = ItemFactory.create(
                parent=cls.chapter,
                category='sequential',
            )
            cls.vertical1 = ItemFactory.create(parent=cls.sequential, category='vertical')
            cls.vertical2 = ItemFactory.create(parent=cls.sequential, category='vertical')
            cls.problems = [
                ItemFactory.create(parent=cls.vertical1, category="problem"),
                ItemFactory.create(parent=cls.vertical1, category="problem"),
                ItemFactory.create(parent=cls.vertical1, category="problem"),
                ItemFactory.create(parent=cls.vertical1, category="problem"),
            ]
            cls.multiparent_problem = ItemFactory.create(parent=cls.vertical1, category="problem")
            cls.vertical2.children.append(cls.multiparent_problem.location)
            creator = UserFactory()
            cls.store.update_item(cls.vertical2, creator.id)
            cls.store.update_item(cls.course, creator.id)

    @skip_unless_lms
    def test_marking_blocks_complete(self):
        self.submit_completion_for(self.problems[0], 0.75)
        self.assert_expected_values({
            self.vertical1: (0.75, 5.0),
            self.vertical2: (0.0, 1.0),
            self.sequential: (0.75, 6.0),
            self.chapter: (0.75, 6.0),
        })

    @skip_unless_lms
    def test_dag_block_values_summed(self):
        self.submit_completion_for(self.multiparent_problem, 1.0)
        self.assert_expected_values({
            self.vertical1: (1.0, 5.0),
            self.vertical2: (1.0, 1.0),
            self.sequential: (2.0, 6.0),
            self.chapter: (2.0, 6.0),
        })

    @skip_unless_lms
    def test_modify_existing_completion(self):
        """
        After updating already-existing completion values, the new values take
        effect, and existing aggregators still exist, even if they are empty.
        """
        self.submit_completion_for(self.problems[2], 0.8)
        self.submit_completion_for(self.multiparent_problem, 0.25)
        self.submit_completion_for(self.problems[2], 0.5)
        self.submit_completion_for(self.multiparent_problem, 0.0)
        self.assert_expected_values({
            self.vertical1: (0.5, 5.0),
            self.vertical2: (0.0, 1.0),
            self.sequential: (0.5, 6.0),
            self.chapter: (0.5, 6.0),
        })

    @skip_unless_lms
    def test_multiple_users(self):
        self.submit_completion_with_user(self.user, self.problems[2], 1.0)
        self.submit_completion_with_user(self.user, self.multiparent_problem, 0.5)

        user2 = UserFactory.create()
        self.submit_completion_with_user(user2, self.problems[0], 1.0)
        self.submit_completion_with_user(user2, self.problems[1], 1.0)
        self.submit_completion_with_user(user2, self.problems[2], 1.0)
        self.submit_completion_with_user(user2, self.problems[3], 1.0)

        self.assert_expected_values({
            self.vertical1: (1.5, 5.0),
            self.vertical2: (0.5, 1.0),
            self.sequential: (2.0, 6.0),
            self.chapter: (2.0, 6.0),
        }, user=self.user)

        self.assert_expected_values({
            self.vertical1: (4.0, 5.0),
            self.vertical2: (0.0, 1.0),
            self.sequential: (4.0, 6.0),
            self.chapter: (4.0, 6.0),
        }, user=user2)


class HiddenContentTestCase(_BaseTestCase):
    """
    Test that hidden content is still counted in aggregators
    """

    @classmethod
    def setUpClass(cls):
        super(HiddenContentTestCase, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.course_key = cls.course.id
        with cls.store.bulk_operations(cls.course.id):
            cls.chapter = ItemFactory.create(
                parent=cls.course,
                category="chapter",
            )
            cls.sequential = ItemFactory.create(
                parent=cls.chapter,
                category='sequential',
                due=timezone.now() - timedelta(days=1),
                hide_after_due=True,
            )
            cls.vertical = ItemFactory.create(parent=cls.sequential, category='vertical')
            cls.htmlblock = ItemFactory.create(parent=cls.vertical, category="html")

    @skip_unless_lms
    def test_hidden_content_still_calculated(self):
        self.submit_completion_for(self.htmlblock, 1.0)
        self.assert_expected_values({
            self.vertical: (1.0, 1.0),
            self.sequential: (1.0, 1.0),
            self.chapter: (1.0, 1.0),
        })


class LibraryTestCase(_BaseTestCase):
    """
    Test handling of library content by completion infrastructure.
    """

    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):

        super(LibraryTestCase, cls).setUpClass()

        cls.library = LibraryFactory.create(modulestore=cls.store)
        creator = UserFactory()

        cls.library_blocks = [
            ItemFactory.create(
                category="html",
                parent=cls.library,
                parent_location=cls.library.location,
                publish_item=False,
                user_id=creator.id,
                modulestore=cls.store,
            ) for _ in range(3)
        ]
        cls.libtools = LibraryToolsService(cls.store)
        cls.store.update_item(cls.library, creator.id)

        with cls.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, None):
            cls.course = CourseFactory.create(modulestore=cls.store)
            cls.course_key = cls.course.id

            with cls.store.bulk_operations(cls.course_key, emit_signals=False):
                cls.chapter = ItemFactory.create(
                    parent=cls.course,
                    parent_location=cls.course.location,
                    category="chapter",
                    modulestore=cls.store,
                    publish_item=False,
                )
                cls.sequential = ItemFactory.create(
                    parent=cls.chapter,
                    parent_location=cls.chapter.location,
                    category='sequential',
                    modulestore=cls.store,
                    publish_item=False,
                )
                cls.vertical = ItemFactory.create(
                    parent=cls.sequential,
                    parent_location=cls.sequential.location,
                    category='vertical',
                    modulestore=cls.store,
                    publish_item=False,
                )

                cls.lc_block = ItemFactory.create(
                    category="library_content",
                    parent=cls.vertical,
                    parent_location=cls.vertical.location,
                    max_count=2,
                    source_library_id=unicode(cls.library.location.library_key),
                    modulestore=cls.store,
                )
                # copy children from library to content block (LibaryContentDescriptor.tools.update_children?)
                cls.store.update_item(cls.course, creator.id)
                cls.store.update_item(cls.lc_block, creator.id)

    def setUp(self):
        super(LibraryTestCase, self).setUp()
        self.lc_block = self._refresh_children(self.lc_block)
        self.in_course_blocks = [self.store.get_item(child) for child in self.lc_block.children]

    def _refresh_children(self, lib_content_block):
        """
        Refresh the set of children on the library content block, then
        fetch a new copy from the modulestore.
        """
        self.libtools.update_children(lib_content_block, self.user.id)
        return self.store.get_item(lib_content_block.location)

    @skip_unless_lms
    def test_completing_library_content(self):
        for block in self.in_course_blocks:
            self.submit_completion_for(block, 0.75)
        self.assert_expected_values({
            self.vertical: (1.5, 2.0),
            self.chapter: (1.5, 2.0),
        })


class EnrollmentTrackTestCase(_BaseTestCase):
    """
    Test that completion aggregates for blocks that are available to the user's
    enrollment track only.
    """
    @classmethod
    def setUpClass(cls):
        super(EnrollmentTrackTestCase, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.course_key = cls.course.id
        CourseMode.objects.create(course_id=cls.course_key, mode_slug=CourseMode.AUDIT, mode_display_name='Audit')
        CourseMode.objects.create(
            course_id=cls.course_key,
            mode_slug=CourseMode.VERIFIED,
            mode_display_name='Verified',
            min_price=1.5,
        )

        cls.partitions = partitions_service.get_all_partitions_for_course(cls.course)
        verified_track_partition_id = 2  # This is determined by the order CourseMode objects are created.
        with cls.store.bulk_operations(cls.course.id):
            cls.chapter = ItemFactory.create(
                parent=cls.course,
                category="chapter",
            )
            cls.vertical1 = ItemFactory.create(
                parent=cls.chapter,
                category="vertical",
                group_access={ENROLLMENT_TRACK_PARTITION_ID: [verified_track_partition_id]},
            )

            cls.vertical2 = ItemFactory.create(
                parent=cls.chapter,
                category="vertical",
            )
            cls.problem1 = ItemFactory.create(
                parent=cls.vertical1,
                category="problem",
            )
            cls.problem2 = ItemFactory.create(
                parent=cls.vertical2,
                category="problem",
            )
            cls.problem3 = ItemFactory.create(
                parent=cls.vertical2,
                category="problem",
                group_access={ENROLLMENT_TRACK_PARTITION_ID: [verified_track_partition_id]},
            )

    def setUp(self):
        super(EnrollmentTrackTestCase, self).setUp()
        self.audit_user = UserFactory.create(username='audituser')
        self.verified_enrollment = CourseEnrollment.enroll(self.user, self.course_key, mode='verified')
        self.audit_enrollment = CourseEnrollment.enroll(self.audit_user, self.course_key, mode='audit')

    @skip_unless_lms
    def test_user_on_track(self):
        self.submit_completion_with_user(self.user, self.problem1, 1.0)
        self.submit_completion_with_user(self.user, self.problem2, 0.5)
        self.submit_completion_with_user(self.user, self.problem3, 0.25)
        self.assert_expected_values({
            self.vertical1: (1.0, 1.0),
            self.vertical2: (0.75, 2.0),
            self.chapter: (1.75, 3.0),
        }, user=self.user)

    @skip_unless_lms
    def test_user_off_track(self):
        self.submit_completion_with_user(self.audit_user, self.problem2, 1.0)
        self.assert_expected_values({
            self.vertical2: (1.0, 1.0),
            self.chapter: (1.0, 1.0),
        }, user=self.audit_user)

    @skip_unless_lms
    def test_user_upgrades(self):
        self.submit_completion_with_user(self.audit_user, self.problem2, 1.0)
        self.audit_enrollment.update_enrollment(mode='verified')
        self.assert_expected_values({
            self.vertical2: (1.0, 2.0),
            self.chapter: (1.0, 3.0),
        }, user=self.audit_user)

    @skip_unless_lms
    def test_user_leaves_track(self):
        self.submit_completion_with_user(self.user, self.problem1, 1.0)
        self.submit_completion_with_user(self.user, self.problem2, 0.5)
        self.submit_completion_with_user(self.user, self.problem3, 0.25)
        self.verified_enrollment.update_enrollment(mode='audit')
        self.assert_expected_values({
            self.vertical2: (0.5, 1.0),
            self.chapter: (0.5, 1.0),
        }, user=self.user)
