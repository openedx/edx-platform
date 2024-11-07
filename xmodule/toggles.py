"""
Add Waffle flags to roll out the extracted XBlocks.
Flags will use to toggle between the old and new block quickly
without putting course content or user state at risk.

Ticket: https://github.com/openedx/edx-platform/issues/35308
"""
from edx_toggles.toggles import WaffleFlag

# .. toggle_name: USE_EXTRACTED_WORD_CLOUD_BLOCK
# .. toggle_description: Enables the use of the extracted Word Cloud XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_warning: Not production-ready until https://github.com/openedx/edx-platform/issues/34840 is done.
# .. toggle_use_cases: temporary
# .. toggle_default: False
# .. toggle_implementation:
# .. toggle_creation_date: 10th Nov, 2024
USE_EXTRACTED_WORD_CLOUD_BLOCK = WaffleFlag('xmodule.use_extracted_block.word_cloud', __name__)
# .. toggle_name: USE_EXTRACTED_ANNOTATABLE_BLOCK
# .. toggle_description: Enables the use of the extracted annotatable XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_warning: Not production-ready until https://github.com/openedx/edx-platform/issues/34841 is done.
# .. toggle_use_cases: temporary
# .. toggle_default: False
# .. toggle_implementation:
# .. toggle_creation_date: 10th Nov, 2024
USE_EXTRACTED_ANNOTATABLE_BLOCK = WaffleFlag('xmodule.use_extracted_block.annotatable', __name__)
# .. toggle_name: USE_EXTRACTED_POLL_QUESTION_BLOCK
# .. toggle_description: Enables the use of the extracted poll question XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_warning: Not production-ready until https://github.com/openedx/edx-platform/issues/34839 is done.
# .. toggle_use_cases: temporary
# .. toggle_default: False
# .. toggle_implementation:
# .. toggle_creation_date: 10th Nov, 2024
USE_EXTRACTED_POLL_QUESTION_BLOCK = WaffleFlag('xmodule.use_extracted_block.poll_question', __name__)
# .. toggle_name: USE_EXTRACTED_LTI_BLOCK
# .. toggle_description: Enables the use of the extracted lti XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_warning: Not production-ready until relevant subtask https://github.com/openedx/edx-platform/issues/34827 is done.
# .. toggle_use_cases: temporary
# .. toggle_default: False
# .. toggle_implementation:
# .. toggle_creation_date: 10th Nov, 2024
USE_EXTRACTED_LTI_BLOCK = WaffleFlag('xmodule.use_extracted_block.lti', __name__)
# .. toggle_name: USE_EXTRACTED_HTML_BLOCK
# .. toggle_description: Enables the use of the extracted html XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_warning: Not production-ready until relevant subtask https://github.com/openedx/edx-platform/issues/34827 is done.
# .. toggle_use_cases: temporary
# .. toggle_default: False
# .. toggle_implementation:
# .. toggle_creation_date: 10th Nov, 2024
USE_EXTRACTED_HTML_BLOCK = WaffleFlag('xmodule.use_extracted_block.html', __name__)
# .. toggle_name: USE_EXTRACTED_DISCUSSION_BLOCK
# .. toggle_description: Enables the use of the extracted discussion XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_warning: Not production-ready until relevant subtask https://github.com/openedx/edx-platform/issues/34827 is done.
# .. toggle_use_cases: temporary
# .. toggle_default: False
# .. toggle_implementation:
# .. toggle_creation_date: 10th Nov, 2024
USE_EXTRACTED_DISCUSSION_BLOCK = WaffleFlag('xmodule.use_extracted_block.discussion', __name__)
# .. toggle_name: USE_EXTRACTED_PROBLEM_BLOCK
# .. toggle_description: Enables the use of the extracted problem XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_warning: Not production-ready until relevant subtask https://github.com/openedx/edx-platform/issues/34827 is done.
# .. toggle_use_cases: temporary
# .. toggle_default: False
# .. toggle_implementation:
# .. toggle_creation_date: 10th Nov, 2024
USE_EXTRACTED_PROBLEM_BLOCK = WaffleFlag('xmodule.use_extracted_block.problem', __name__)
# .. toggle_name: USE_EXTRACTED_VIDEO_BLOCK
# .. toggle_description: Enables the use of the extracted video XBlock, which has been shifted to the 'openedx/xblocks-contrib' repo.
# .. toggle_warning: Not production-ready until relevant subtask https://github.com/openedx/edx-platform/issues/34827 is done.
# .. toggle_use_cases: temporary
# .. toggle_default: False
# .. toggle_implementation:
# .. toggle_creation_date: 10th Nov, 2024
USE_EXTRACTED_VIDEO_BLOCK = WaffleFlag('xmodule.use_extracted_block.video', __name__)
