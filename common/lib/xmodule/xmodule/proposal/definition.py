
# A way to specify what parameters a type of definition can accept.
#   name -- str
#   default -- default value, or None if there isn't one.  If there is no default value,
#        the parameter is required.
#   is_valid -- str -> bool A general way of specifying parameter
#        types, though perhaps a more restricted but explicit
#        structure is better instead/in addition.
#   is_inherited -- should settings for this param inherit?
ModuleParameter = NamedTuple('ModuleParameter', 'name default is_valid is_inherited')

class XModuleDefinition(object):
    @property
    def accepted_parameters(self):
        """
        Return a list of ModuleParameters.
        """
        pass

    @property
    def required_capabilities(self):
        """
        Returns a list of methods that the FOOSystem must support in
        order to be used with this kind of definition.  If this is a
        container module, needs to be a union of all the descendents,
        and so may change as children get added, removed, or changed.
        """
        pass

    @property
    def child_locations(self):
        """Return a list of child locations for this definition"""
        pass

