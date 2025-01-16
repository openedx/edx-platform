import json
from tempfile import NamedTemporaryFile
from unittest.mock import Mock
from common.djangoapps.student.tests.factories import UserFactory
import pytest
from unittest import mock



# Mock course key
mock_course_key = Mock()
mock_course_key_string = "course-v1:edX+DemoX+Demo_Course"

# Mock vertical blocks and URLs
mock_verticals = [
    Mock(get_children=lambda: [Mock(usage_key="block-v1:edX+DemoX+Demo_Course+type@vertical+block@1")]),
    Mock(get_children=lambda: [Mock(usage_key="block-v1:edX+DemoX+Demo_Course+type@vertical+block@2")])
]

# Mock URLs
mock_urls = [
    ["block-v1:edX+DemoX+Demo_Course+type@vertical+block@1", "http://example.com/valid"],
    ["block-v1:edX+DemoX+Demo_Course+type@vertical+block@2", "http://example.com/invalid"]
]

# Mock URL validation responses
mock_responses = [
  {
    "block_id": "block-v1:edX+DemoX+Demo_Course+type@vertical+block@1",
    "url": "http://example.com/valid",
    "status": 200
  },
  {
    "block_id": "block-v1:edX+DemoX+Demo_Course+type@vertical+block@2",
    "url": "http://example.com/invalid",
    "status": 404
  }
]

# Mock JSON file creation
# mock_json_file = NamedTemporaryFile(prefix="course-v1:edX+DemoX+Demo_Course.", suffix=".json")
# mock_json_content = json.dumps(mock_responses, indent=4)
# mock_json_file.write(mock_json_content.encode())

