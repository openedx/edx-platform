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
USE_EXTRACTED_WORD_CLOUD_BLOCK = WaffleFlag('xmodule.use_extracted_block.word_cloud', __name__)
# TODO: Add flag docs once above approved
USE_EXTRACTED_ANNOTATABLE_BLOCK = WaffleFlag('xmodule.use_extracted_block.annotatable', __name__)
USE_EXTRACTED_POLL_BLOCK = WaffleFlag('xmodule.use_extracted_block.poll', __name__)
USE_EXTRACTED_LTI_BLOCK = WaffleFlag('xmodule.use_extracted_block.lti', __name__)
USE_EXTRACTED_HTML_BLOCK = WaffleFlag('xmodule.use_extracted_block.html', __name__)
USE_EXTRACTED_DISCUSSION_BLOCK = WaffleFlag('xmodule.use_extracted_block.discussion', __name__)
USE_EXTRACTED_PROBLEM_BLOCK = WaffleFlag('xmodule.use_extracted_block.problem', __name__)
USE_EXTRACTED_VIDEO_BLOCK = WaffleFlag('xmodule.use_extracted_block.video', __name__)
