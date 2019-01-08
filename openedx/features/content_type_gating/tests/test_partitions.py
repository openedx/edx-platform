from datetime import datetime
from mock import Mock, patch

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from openedx.features.content_type_gating.helpers import CONTENT_GATING_PARTITION_ID
from openedx.features.content_type_gating.partitions import create_content_gating_partition
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from xmodule.partitions.partitions import UserPartitionError


class TestContentTypeGatingPartition(CacheIsolationTestCase):
    def setUp(self):
        self.course_key = CourseKey.from_string('course-v1:test+course+key')

    def test_create_content_gating_partition_happy_path(self):

        mock_course = Mock(id=self.course_key, user_partitions={})
        ContentTypeGatingConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))

        with patch('openedx.features.content_type_gating.partitions.ContentTypeGatingPartitionScheme.create_user_partition') as mock_create:
            partition = create_content_gating_partition(mock_course)
            self.assertEqual(partition, mock_create.return_value)

    def test_create_content_gating_partition_override_only(self):
        mock_course = Mock(id=self.course_key, user_partitions={})
        ContentTypeGatingConfig.objects.create(enabled=False, studio_override_enabled=True)

        partition = create_content_gating_partition(mock_course)
        self.assertIsNotNone(partition)

    def test_create_content_gating_partition_disabled(self):
        mock_course = Mock(id=self.course_key, user_partitions={})
        ContentTypeGatingConfig.objects.create(enabled=False, studio_override_enabled=False)

        partition = create_content_gating_partition(mock_course)
        self.assertIsNone(partition)

    def test_create_content_gating_partition_no_scheme_installed(self):
        mock_course = Mock(id=self.course_key, user_partitions={})
        ContentTypeGatingConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))

        with patch('openedx.features.content_type_gating.partitions.UserPartition.get_scheme', side_effect=UserPartitionError):
            partition = create_content_gating_partition(mock_course)

        self.assertIsNone(partition)

    def test_create_content_gating_partition_partition_id_used(self):
        mock_course = Mock(id=self.course_key, user_partitions={Mock(name='partition', id=CONTENT_GATING_PARTITION_ID): object()})
        ContentTypeGatingConfig.objects.create(enabled=True, enabled_as_of=datetime(2018, 1, 1))

        with patch('openedx.features.content_type_gating.partitions.LOG') as mock_log:
            partition = create_content_gating_partition(mock_course)
            mock_log.warning.assert_called()
        self.assertIsNone(partition)
