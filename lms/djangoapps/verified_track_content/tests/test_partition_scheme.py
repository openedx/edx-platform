from django.test import TestCase
from nose.plugins.attrib import attr

from ..partition_scheme import EnrollmentTrackPartitionScheme
from course_modes.models import CourseMode

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.partitions.partitions import UserPartition


class VerificationTrackUserPartitionTest(SharedModuleStoreTestCase):

    @classmethod
    def setUpClass(cls):
        super(VerificationTrackUserPartitionTest, cls).setUpClass()
        cls.course = CourseFactory.create()
        cls.user_partition = EnrollmentTrackPartitionScheme.create_user_partition(
            1,
            "partition",
            "test enrollment track partition",
            parameters={"course_id": unicode(cls.course.id)}
        )

    def test_only_default_mode(self):
        groups = self.user_partition.groups
        self.assertEqual(1, len(groups))
        self.assertEqual("audit", groups[0].name)

    def test_multiple_groups(self):
        self.create_mode(CourseMode.AUDIT, "Audit Enrollment Track", min_price=0)
        self.create_mode(CourseMode.VERIFIED, "Verified Enrollment Track", min_price=1)
        self.create_mode(CourseMode.PROFESSIONAL, "Professional Enrollment Track", min_price=2)

        groups = self.user_partition.groups
        self.assertEqual(3, len(groups))
        self.assertEqual("audit", groups[0].name)


    def create_mode(self, mode_slug, mode_name, min_price=0):
        """
        Create a new course mode
        """
        return CourseMode.objects.get_or_create(
            course_id=self.course.id,
            mode_display_name=mode_name,
            mode_slug=mode_slug,
            min_price=min_price,
            suggested_prices='',
            currency='usd'
        )


@attr(shard=2)
class TestExtension(TestCase):
    """
    Ensure that the scheme extension is correctly plugged in (via entry point in setup.py)
    """

    def test_get_scheme(self):
        self.assertEquals(UserPartition.get_scheme('enrollment_track'), EnrollmentTrackPartitionScheme)
