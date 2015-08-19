"""
Namespace that defines fields common to all blocks used in the LMS
"""
from lazy import lazy

from xblock.fields import Boolean, Scope, String, XBlockMixin, Dict
from xblock.validation import ValidationMessage
from xmodule.modulestore.inheritance import UserPartitionList
from xmodule.partitions.partitions import NoSuchUserPartitionError, NoSuchUserPartitionGroupError

# Make '_' a no-op so we can scrape strings
_ = lambda text: text


class GroupAccessDict(Dict):
    """Special Dict class for serializing the group_access field"""
    def from_json(self, access_dict):
        if access_dict is not None:
            return {int(k): access_dict[k] for k in access_dict}

    def to_json(self, access_dict):
        if access_dict is not None:
            return {unicode(k): access_dict[k] for k in access_dict}


class LmsBlockMixin(XBlockMixin):
    """
    Mixin that defines fields common to all blocks used in the LMS
    """
    hide_from_toc = Boolean(
        help=_("Whether to display this module in the table of contents"),
        default=False,
        scope=Scope.settings
    )
    format = String(
        # Translators: "TOC" stands for "Table of Contents"
        help=_("What format this module is in (used for deciding which "
               "grader to apply, and what to show in the TOC)"),
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
    group_access = GroupAccessDict(
        help=_(
            "A dictionary that maps which groups can be shown this block. The keys "
            "are group configuration ids and the values are a list of group IDs. "
            "If there is no key for a group configuration or if the set of group IDs "
            "is empty then the block is considered visible to all. Note that this "
            "field is ignored if the block is visible_to_staff_only."
        ),
        default={},
        scope=Scope.settings,
    )

    @lazy
    def merged_group_access(self):
        """
        This computes access to a block's group_access rules in the context of its position
        within the courseware structure, in the form of a lazily-computed attribute.
        Each block's group_access rule is merged recursively with its parent's, guaranteeing
        that any rule in a parent block will be enforced on descendants, even if a descendant
        also defined its own access rules.  The return value is always a dict, with the same
        structure as that of the group_access field.

        When merging access rules results in a case where all groups are denied access in a
        user partition (which effectively denies access to that block for all students),
        the special value False will be returned for that user partition key.
        """
        parent = self.get_parent()
        if not parent:
            return self.group_access or {}

        merged_access = parent.merged_group_access.copy()
        if self.group_access is not None:
            for partition_id, group_ids in self.group_access.items():
                if group_ids:  # skip if the "local" group_access for this partition is None or empty.
                    if partition_id in merged_access:
                        if merged_access[partition_id] is False:
                            # special case - means somewhere up the hierarchy, merged access rules have eliminated
                            # all group_ids from this partition, so there's no possible intersection.
                            continue
                        # otherwise, if the parent defines group access rules for this partition,
                        # intersect with the local ones.
                        merged_access[partition_id] = list(
                            set(merged_access[partition_id]).intersection(group_ids)
                        ) or False
                    else:
                        # add the group access rules for this partition to the merged set of rules.
                        merged_access[partition_id] = group_ids
        return merged_access

    # Specified here so we can see what the value set at the course-level is.
    user_partitions = UserPartitionList(
        help=_("The list of group configurations for partitioning students in content experiments."),
        default=[],
        scope=Scope.settings
    )

    def _get_user_partition(self, user_partition_id):
        """
        Returns the user partition with the specified id.  Raises
        `NoSuchUserPartitionError` if the lookup fails.
        """
        for user_partition in self.user_partitions:
            if user_partition.id == user_partition_id:
                return user_partition

        raise NoSuchUserPartitionError("could not find a UserPartition with ID [{}]".format(user_partition_id))

    def validate(self):
        """
        Validates the state of this xblock instance.
        """
        _ = self.runtime.service(self, "i18n").ugettext  # pylint: disable=redefined-outer-name
        validation = super(LmsBlockMixin, self).validate()
        has_invalid_user_partitions = False
        has_invalid_groups = False
        for user_partition_id, group_ids in self.group_access.iteritems():
            try:
                user_partition = self._get_user_partition(user_partition_id)
            except NoSuchUserPartitionError:
                has_invalid_user_partitions = True
            else:
                # Skip the validation check if the partition has been disabled
                if user_partition.active:
                    for group_id in group_ids:
                        try:
                            user_partition.get_group(group_id)
                        except NoSuchUserPartitionGroupError:
                            has_invalid_groups = True

        if has_invalid_user_partitions:
            validation.add(
                ValidationMessage(
                    ValidationMessage.ERROR,
                    _(u"This component refers to deleted or invalid content group configurations.")
                )
            )
        if has_invalid_groups:
            validation.add(
                ValidationMessage(
                    ValidationMessage.ERROR,
                    _(u"This component refers to deleted or invalid content groups.")
                )
            )
        return validation
