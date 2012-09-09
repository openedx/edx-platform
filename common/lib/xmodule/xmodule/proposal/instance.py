class XModuleInstance(object):
    """
    An instance of a particular XModuleDefinition, with particular
    policy, in the context of a course.
    """

    def __init__(self, id, definition):
        """
        id -- an instance_id : name for this instance; unique within a course.
        definition -- a XModuleDefinition

        """
        self.id = id
        self._definition = definition

    @property
    def definition(self):
        """
        Return the XModuleDefinition for this instance
        """
        pass

    def get_parameter(self, param_name):
        """
        Return the value of param_name for this instance.  param_name must be
        in for self.definition.accepted_parameters.
        """
        pass

    def get_children_ids(self):
        """
        return the list of module_ids for the children of this instance.
        """
        pass


    @property
    def parent_id(self):
        """
        Return the instance_id of this instance's parent, or None if
        this is the course root.

        Always well defined because instances only appear once in the
        course tree structure.
        """
        pass

    @property
    def stores_state(self):
        """
        Does this instance store state?  The reasoning behind putting
        this on the instance rather than the definition is that I can
        imagine cases where some problems may store state in some
        cases, and not in others.  This may not be worth supporting.
        """
        pass


    def get_sample_state(self):
        """
        Needed for cms.
        """
        pass


    def max_score(self):
        """
        Can we move this to instance-level from module level?  Would
        make various grading things easier if grades were consistent
        accross all students for any given instance.  Perhaps not...
        """
        pass

    ## To / from storage ########################################################

    # all an instance is in storage is a tuple (instance_id, definition_location, children_ids)

    # The definition is looked up via definition_location, the policy
    # via instance_id.  The children_ids are pointers to instances,
    # which must correspond to the definition's children. [do not like?]

    # ??? to/from xml, json?

