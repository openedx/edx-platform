"""
Expose NexBlock instances in courseware through the NexWrapperBlock.
"""

import logging
from uuid import uuid4

from xblock.core import XBlock
from xblock.fields import Dict, Scope, String
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
class NexWrapperBlock(
    XBlock, StudioEditableXBlockMixin
):  # lint-amnesty, pylint: disable=abstract-method
    """
    A block type to expose an instance of a NexBlock.

    Settings-scoped fields ares stored authoritatively here (to allow editing
    via Studio), but are pushed to NexBlockInstance data upon course publish,
    so they are never read from here in an LMS context.

    Learner state is stored in NexBlockLearnerData model instead of in the XBlock.

    Usages of this block and instance of NexBlocks are related by the UUID.
    """

    package = String(
        display_name=_("NexBlock package"),
        help=_("An npm-installable package name/path to NexBlock JS code"),
        scope=Scope.settings,
    )
    uuid = String(
        display_name=_("Instance UUID"),
        help=_(
            "Globally unique ID of a this NexBlock instance. "
            "Editing this will change the underlying instance"
        ),
        scope=Scope.settings,
        default=str(uuid4()),
    )
    # TODO: do we need this?
    # slug = String(
    #     display_name=_("URL slug for block"),
    #     help_text=_(
    #         "URL-safe identifier for NexBlock. Alphanumeric, dashes, and underscores."
    #     ),
    #     scope=Scope.settings,
    # )
    display_name = Dict(
        display_name=_("User-friendly display name of block"),
        scope=Scope.settings,
    )
    instance_data = Dict(
        display_name=_("NexBlock instance data JSON"),
        help=_("Settings for this instance of a NexBlock"),
        scope=Scope.settings,
        default={},
    )
    # TODO: I think we can remove this.
    # learner_data = Dict(
    #    display_name=_("NexBlock learner data JSON"),
    #    help=_("Data for this instance of a NexBlock for a particular learner"),
    #    scope=Scope.user_state,
    #    default={},
    # )

    editable_fields = ["package", "uuid", "slug", "display_name", "instance_data"]

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

    def student_view(self, context=None):
        """
        Renders student view for LMS.
        """
        raise NotImplementedError

    def author_view(self, context=None):  # pylint: disable=unused-argument
        """
        Renders author view for Studio.
        """
        raise NotImplementedError

    def student_view_data(self):
        """
        Returns a JSON representation of the student_view of this XBlock.
        """
        raise NotImplementedError

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Parses OLX into XBlock.
        """
        raise NotImplementedError
