# -*- coding: utf-8 -*-
"""
NexBlock-framework-as-an-XBlock prototype.
"""

import logging

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
class NexBlock(
    XBlock, StudioEditableXBlockMixin
):  # lint-amnesty, pylint: disable=abstract-method
    """
    Instance of a NexBlock.
    """

    path = String(
        display_name=_("npm-installable path of NexBlock code"),
        scope=Scope.content,
    )
    instance_data = Dict(
        display_name=_("Settings for this instance of a NexBlock"),
        scope=Scope.content,
        default={},
    )
    learner_data = Dict(
        disply_name=_("Data for this instance of a NexBlock for a particular learner"),
        scope=Scope.user_state,
        default={},
    )

    editable_fields = []  # @@TODO

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
