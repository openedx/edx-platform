"""
Expose NexBlock instances in courseware through the NexWrapperBlock.
"""

import logging
from uuid import uuid4

from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Boolean, Dict, Scope, String
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)  # pylint: disable=invalid-name


def _(text):
    """
    A noop underscore function that marks strings for extraction.
    """
    return text


@XBlock.needs("user")
@XBlock.needs("i18n")
class NexBlockWrapperBlock(
    XBlock, StudioEditableXBlockMixin
):  # lint-amnesty, pylint: disable=abstract-method
    """
    A block type to expose an instance of a NexBlock.

    Instance data is stored here(to allow editing via Studio).
    Learner state is stored in NexBlockLearnerData model instead of in the XBlock.

    Usages of this block and instance of NexBlocks are related by the UUID.
    """

    display_name = String(
        display_name=_("Display Name"),
        help=_("The display name for this component."),
        default="NexBlock",
        scope=Scope.settings,
    )
    nexblock_remote_url = String(
        display_name=_("NexBlock Remote URL"),
        help=_("A path to a Webpack Federation remote that is hosting NexBlocks."),
        scope=Scope.settings,
        default="http://localhost:8080/remoteEntry.js",
    )
    nexblock_type = String(
        display_name=_("NexBlock Type"),
        help=_("Name of a NexBlock type."),
        scope=Scope.settings,
        default="Announcement",
    )
    instance_data = Dict(
        display_name=_("Instance Data"),
        help=_("Instance-level settings for this NexBlock instance, as JSON."),
        scope=Scope.settings,
        default={},
    )
    integrity_protected = Boolean(
        display_name=_("Integrity-Protected?"),
        help=_(
            "Whether settings are restricted from user. Enabling this disables offline usage."
        ),
        scope=Scope.settings,
        default=False,
    )

    editable_fields = [
        "display_name",
        "nexblock_remote_url",
        "nexblock_type",
        "instance_data",
        "integrity_protected",
    ]

    has_author_view = True  # Tells Studio to use author_view

    @property
    def course_key(self):
        """
        :return: int course id

        NB: The goal is to move this XBlock out of edx-platform, and so we use
        scope_ids.usage_id instead of runtime.course_id so that the code will
        continue to work with workbench-based testing.
        """
        return getattr(self.scope_ids.usage_id, "course_key", None)

    @property
    def django_user(self):
        """
        Returns django user associated with user currently interacting
        with the XBlock.
        """
        user_service = self.runtime.service(self, "user")
        if not user_service:
            return None
        return user_service._django_user  # pylint: disable=protected-access

    def _view(self):
        """
        TODO
        """
        iframe_unique_id = f"nexblock-iframe-{uuid4()}"
        iframe_styles = """
            width: 100%;
            height: 500px;
            border: none;
        """
        mfe_root = "http://localhost:2000"
        usage_id = str(self.scope_ids.usage_id)
        renderer_url = (
            f"{mfe_root}/nexblock"
            f"?url={self.nexblock_remote_url}"
            f"&view={self.nexblock_type}"
            f"&usage_id={usage_id}"
        )
        iframe_html = f"""
            <iframe class="nexblock-iframe"
                    id="{iframe_unique_id}"
                    src="{renderer_url}"
                    style="{iframe_styles}"
            ></iframe>
        """
        fragment = Fragment()
        fragment.add_content(iframe_html)
        return fragment

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """
        Renders student view for LMS.

        TODO
        """
        return self._view()

    def author_view(self, context=None):  # pylint: disable=unused-argument
        """
        Renders preview view for Studio.

        TODO
        """
        fragment = Fragment()
        fragment.add_content(
            f"<p>This will soon show a NexBlock of type <strong>{self.nexblock_type}</strong><p>"
        )
        return fragment
