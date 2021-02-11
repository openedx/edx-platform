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
    package = String(
        display_name=_("Package"),
        help=_("An npm-installable package of NexBlock code."),
        scope=Scope.settings,
        default="git+https://github.com/kdmccormick/nexblock-test-announcement.git",
    )
    integrity_protected = Boolean(
        display_name=_("Integrity-Protected?"),
        help=_(
            "Whether settings are restricted from user. Enabling this disables offline usage."
        ),
        scope=Scope.settings,
        default=False,
    )
    instance_data = Dict(
        display_name=_("Instance Data"),
        help=_("Instance-level settings for this NexBlock instance, as JSON."),
        scope=Scope.settings,
        default={},
    )

    editable_fields = [
        "display_name",
        "package",
        "integrity_protected",
        "instance_data",
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

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """
        Renders student view for LMS.

        TODO
        """
        iframe_unique_id = f"nexblock-iframe-{uuid4()}"
        iframe_styles = """
            width: 100%;
            height: 500px;
            border: none;
        """
        renderer_url = "http://localhost:2000/nexblock"
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

    def author_view(self, context=None):  # pylint: disable=unused-argument
        """
        Renders preview view for Studio.

        TODO
        """
        fragment = Fragment()
        fragment.add_content(
            f"<p>This will soon show a NexBlock of type <strong>{self.package}</strong><p>"
        )
        return fragment
