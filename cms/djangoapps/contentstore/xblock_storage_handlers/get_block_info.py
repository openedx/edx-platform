

import logging
from datetime import datetime
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import (User)  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.timezone import timezone
from django.utils.translation import gettext as _
from edx_django_utils.plugins import pluggable_override
from openedx_events.content_authoring.data import DuplicatedXBlockData
from openedx_events.content_authoring.signals import XBLOCK_DUPLICATED
from edx_proctoring.api import (
    does_backend_support_onboarding,
    get_exam_by_content_id,
    get_exam_configuration_dashboard_url,
)
from edx_proctoring.exceptions import ProctoredExamNotFoundException
from help_tokens.core import HelpUrlExpert
from lti_consumer.models import CourseAllowPIISharingInLTIFlag
from opaque_keys.edx.locator import LibraryUsageLocator
from pytz import UTC
from xblock.core import XBlock
from xblock.fields import Scope

from cms.djangoapps.contentstore.config.waffle import SHOW_REVIEW_RULES_FLAG
from cms.djangoapps.models.settings.course_grading import CourseGradingModel
from common.djangoapps.edxmako.services import MakoService
from common.djangoapps.static_replace import replace_static_urls
from common.djangoapps.student.auth import (
    has_studio_read_access,
    has_studio_write_access,
)
from common.djangoapps.util.date_utils import get_default_time_display
from common.djangoapps.util.json_request import JsonResponse, expect_json
from common.djangoapps.xblock_django.user_service import DjangoXBlockUserService
from openedx.core.djangoapps.bookmarks import api as bookmarks_api
from openedx.core.djangoapps.discussions.models import DiscussionsConfiguration
from openedx.core.djangoapps.video_config.toggles import PUBLIC_VIDEO_SHARE
from openedx.core.lib.gating import api as gating_api
from openedx.core.toggles import ENTRANCE_EXAMS
from xmodule.course_block import (
    DEFAULT_START_DATE,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.library_tools import (
    LibraryToolsService,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore import (
    EdxJSONEncoder,
    ModuleStoreEnum,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.django import (
    modulestore,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.draft_and_published import (
    DIRECT_ONLY_CATEGORIES,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.exceptions import (
    InvalidLocationError,
    ItemNotFoundError,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.inheritance import (
    own_metadata,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.services import (
    ConfigurationService,
    SettingsService,
    TeamsConfigurationService,
)  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.tabs import (
    CourseTabList,
)  # lint-amnesty, pylint: disable=wrong-import-order

from ..utils import (
    ancestor_has_staff_lock,
    find_release_date_source,
    find_staff_lock_source,
    get_split_group_display_name,
    get_user_partition_info,
    get_visibility_partition_info,
    has_children_visible_to_specific_partition_groups,
    is_currently_visible_to_students,
    is_self_paced,
)

from .create_xblock import create_xblock
from .usage_key_with_run import usage_key_with_run
from ..helpers import (
    get_parent_xblock,
    import_staged_content_from_user_clipboard,
    is_unit,
    xblock_primary_child_category,
    xblock_studio_url,
    xblock_type_display_name,
)

from .helpers import (
    add_container_page_publishing_info,
)
from .create_xblock_info import create_xblock_info


def get_block_info(
    xblock,
    rewrite_static_links=True,
    include_ancestor_info=False,
    include_publishing_info=False,
):
    """
    metadata, data, id representation of a leaf block fetcher.
    :param usage_key: A UsageKey
    """
    with modulestore().bulk_operations(xblock.location.course_key):
        data = getattr(xblock, "data", "")
        if rewrite_static_links:
            data = replace_static_urls(data, None, course_id=xblock.location.course_key)

        # Pre-cache has changes for the entire course because we'll need it for the ancestor info
        # Except library blocks which don't [yet] use draft/publish
        if not isinstance(xblock.location, LibraryUsageLocator):
            modulestore().has_changes(
                modulestore().get_course(xblock.location.course_key, depth=None)
            )

        # Note that children aren't being returned until we have a use case.
        xblock_info = create_xblock_info(
            xblock,
            data=data,
            metadata=own_metadata(xblock),
            include_ancestor_info=include_ancestor_info,
        )
        if include_publishing_info:
            add_container_page_publishing_info(xblock, xblock_info)

        return xblock_info
