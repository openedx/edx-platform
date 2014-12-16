"""
Namespace that defines fields common to all blocks used in the LMS
"""
from xblock.fields import Boolean, Scope, String, XBlockMixin, Dict
from xblock.validation import ValidationMessage
from xmodule.modulestore.inheritance import UserPartitionList

# Make '_' a no-op so we can scrape strings
_ = lambda text: text


class LmsBlockMixin(XBlockMixin):
    """
    Mixin that defines fields common to all blocks used in the LMS
    """
    hide_from_toc = Boolean(
        help="Whether to display this module in the table of contents",
        default=False,
        scope=Scope.settings
    )
    format = String(
        help="What format this module is in (used for deciding which "
             "grader to apply, and what to show in the TOC)",
        scope=Scope.settings,
    )
    chrome = String(
        display_name=_("Courseware Chrome"),
        help=_("Enter the chrome, or navigation tools, to use for the XBlock in the LMS. Valid values are: \n"
               "\"chromeless\" -- to not use tabs or the accordion; \n"
               "\"tabs\" -- to use tabs only; \n"
               "\"accordion\" -- to use the accordion only; or \n"
               "\"tabs,accordion\" -- to use tabs and the accordion."),
        scope=Scope.settings,
        default=None,
    )
    default_tab = String(
        display_name=_("Default Tab"),
        help=_("Enter the tab that is selected in the XBlock. If not set, the Courseware tab is selected."),
        scope=Scope.settings,
        default=None,
    )
    source_file = String(
        display_name=_("LaTeX Source File Name"),
        help=_("Enter the source file name for LaTeX."),
        scope=Scope.settings,
        deprecated=True
    )
    ispublic = Boolean(
        display_name=_("Course Is Public"),
        help=_("Enter true or false. If true, the course is open to the public. If false, the course is open only to admins."),
        scope=Scope.settings
    )
    visible_to_staff_only = Boolean(
        help=_("If true, can be seen only by course staff, regardless of start date."),
        default=False,
        scope=Scope.settings,
    )
    group_access = Dict(
        help="A dictionary that maps which groups can be shown this block. The keys "
             "are group configuration ids and the values are a list of group IDs. "
             "If there is no key for a group configuration or if the list of group IDs "
             "is empty then the block is considered visible to all. Note that this "
             "field is ignored if the block is visible_to_staff_only.",
        default={},
        scope=Scope.settings,
    )

    # Specified here so we can see what the value set at the course-level is.
    user_partitions = UserPartitionList(
        help=_("The list of group configurations for partitioning students in content experiments."),
        default=[],
        scope=Scope.settings
    )

    def _get_user_partition(self, user_partition_id):
        """
        Returns the user partition with the specified id, or None if there is no such partition.
        """
        for user_partition in self.user_partitions:
            if user_partition.id == user_partition_id:
                return user_partition

        return None

    def is_visible_to_group(self, user_partition, group):
        """
        Returns true if this xblock should be shown to a user in the specified user partition group.
        This method returns true if one of the following is true:
         - the xblock has no group_access dictionary specified
         - if the dictionary has no key for the user partition's id
         - if the value for the user partition's id is an empty list
         - if the value for the user partition's id contains the specified group's id
        """
        if not self.group_access:
            return True
        group_ids = self.group_access.get(user_partition.id, [])
        if len(group_ids) == 0:
            return True
        return group.id in group_ids

    def validate(self):
        """
        Validates the state of this xblock instance.
        """
        _ = self.runtime.service(self, "i18n").ugettext  # pylint: disable=redefined-outer-name
        validation = super(LmsBlockMixin, self).validate()
        for user_partition_id, group_ids in self.group_access.iteritems():
            user_partition = self._get_user_partition(user_partition_id)
            if not user_partition:
                validation.add(
                    ValidationMessage(
                        ValidationMessage.ERROR,
                        _(u"This xblock refers to a deleted or invalid content group configuration.")
                    )
                )
            else:
                for group_id in group_ids:
                    group = user_partition.get_group(group_id)
                    if not group:
                        validation.add(
                            ValidationMessage(
                                ValidationMessage.ERROR,
                                _(u"This xblock refers to a deleted or invalid content group.")
                            )
                        )

        return validation
