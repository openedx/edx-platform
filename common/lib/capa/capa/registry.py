"""A registry for finding classes based on tags in the class."""


class TagRegistry(object):
    """
    A registry mapping tags to handlers.

    (A dictionary with some extra error checking.)
    """
    def __init__(self):
        self._mapping = {}

    def register(self, cls):
        """
        Register cls as a supported tag type.  It is expected to define cls.tags as a list of tags
        that it implements.

        If an already-registered type has registered one of those tags, will raise ValueError.

        If there are no tags in cls.tags, will also raise ValueError.
        """

        # Do all checks and complain before changing any state.
        if len(cls.tags) == 0:
            raise ValueError("No tags specified for class {0}".format(cls.__name__))

        for tag in cls.tags:
            if tag in self._mapping:
                other_cls = self._mapping[tag]
                if cls == other_cls:
                    # registering the same class multiple times seems silly, but ok
                    continue
                raise ValueError(
                    "Tag {0} already registered by class {1}."
                    " Can't register for class {2}".format(
                        tag,
                        other_cls.__name__,
                        cls.__name__,
                    )
                )

        # Ok, should be good to change state now.
        for t in cls.tags:
            self._mapping[t] = cls

        # Returning the cls means we can use this as a decorator.
        return cls

    def registered_tags(self):
        """
        Get a list of all the tags that have been registered.
        """
        return list(self._mapping.keys())

    def get_class_for_tag(self, tag):
        """
        For any tag in registered_tags(), returns the corresponding class.  Otherwise, will raise
        KeyError.
        """
        return self._mapping[tag]
