"""Defines ``Group`` and ``UserPartition`` models for partitioning"""

from collections import namedtuple
from stevedore.extension import ExtensionManager

# We use ``id`` in this file as the IDs of our Groups and UserPartitions,
# which Pylint disapproves of.
# pylint: disable=invalid-name, redefined-builtin


class UserPartitionError(Exception):
    """
    Base Exception for when an error was found regarding user partitions.
    """
    pass


class NoSuchUserPartitionError(UserPartitionError):
    """
    Exception to be raised when looking up a UserPartition by its ID fails.
    """
    pass


class NoSuchUserPartitionGroupError(UserPartitionError):
    """
    Exception to be raised when looking up a UserPartition Group by its ID fails.
    """
    pass


class Group(namedtuple("Group", "id name")):
    """
    An id and name for a group of students.  The id should be unique
    within the UserPartition this group appears in.
    """
    # in case we want to add to this class, a version will be handy
    # for deserializing old versions.  (This will be serialized in courses)
    VERSION = 1

    def __new__(cls, id, name):
        # pylint: disable=super-on-old-class
        return super(Group, cls).__new__(cls, int(id), name)

    def to_json(self):
        """
        'Serialize' to a json-serializable representation.

        Returns:
            a dictionary with keys for the properties of the group.
        """
        # pylint: disable=no-member
        return {
            "id": self.id,
            "name": self.name,
            "version": Group.VERSION
        }

    @staticmethod
    def from_json(value):
        """
        Deserialize a Group from a json-like representation.

        Args:
            value: a dictionary with keys for the properties of the group.

        Raises TypeError if the value doesn't have the right keys.
        """
        if isinstance(value, Group):
            return value

        for key in ("id", "name", "version"):
            if key not in value:
                raise TypeError("Group dict {0} missing value key '{1}'".format(
                    value, key))

        if value["version"] != Group.VERSION:
            raise TypeError("Group dict {0} has unexpected version".format(
                value))

        return Group(value["id"], value["name"])


# The Stevedore extension point namespace for user partition scheme plugins.
USER_PARTITION_SCHEME_NAMESPACE = 'openedx.user_partition_scheme'


class UserPartition(namedtuple("UserPartition", "id name description groups scheme")):
    """
    A named way to partition users into groups, primarily intended for running
    experiments.  It is expected that each user will be in at most one group in a
    partition.

    A Partition has an id, name, scheme, description, and a list of groups.
    The id is intended to be unique within the context where these are used. (e.g. for
    partitions of users within a course, the ids should be unique per-course).
    The scheme is used to assign users into groups.
    """
    VERSION = 2

    # The collection of user partition scheme extensions.
    scheme_extensions = None

    # The default scheme to be used when upgrading version 1 partitions.
    VERSION_1_SCHEME = "random"

    def __new__(cls, id, name, description, groups, scheme=None, scheme_id=VERSION_1_SCHEME):
        # pylint: disable=super-on-old-class
        if not scheme:
            scheme = UserPartition.get_scheme(scheme_id)
        return super(UserPartition, cls).__new__(cls, int(id), name, description, groups, scheme)

    @staticmethod
    def get_scheme(name):
        """
        Returns the user partition scheme with the given name.
        """
        # Note: we're creating the extension manager lazily to ensure that the Python path
        # has been correctly set up. Trying to create this statically will fail, unfortunately.
        if not UserPartition.scheme_extensions:
            UserPartition.scheme_extensions = ExtensionManager(namespace=USER_PARTITION_SCHEME_NAMESPACE)
        try:
            scheme = UserPartition.scheme_extensions[name].plugin
        except KeyError:
            raise UserPartitionError("Unrecognized scheme {0}".format(name))
        scheme.name = name
        return scheme

    def to_json(self):
        """
        'Serialize' to a json-serializable representation.

        Returns:
            a dictionary with keys for the properties of the partition.
        """
        # pylint: disable=no-member
        return {
            "id": self.id,
            "name": self.name,
            "scheme": self.scheme.name,
            "description": self.description,
            "groups": [g.to_json() for g in self.groups],
            "version": UserPartition.VERSION
        }

    @staticmethod
    def from_json(value):
        """
        Deserialize a Group from a json-like representation.

        Args:
            value: a dictionary with keys for the properties of the group.

        Raises TypeError if the value doesn't have the right keys.
        """
        if isinstance(value, UserPartition):
            return value

        for key in ("id", "name", "description", "version", "groups"):
            if key not in value:
                raise TypeError("UserPartition dict {0} missing value key '{1}'".format(value, key))

        if value["version"] == 1:
            # If no scheme was provided, set it to the default ('random')
            scheme_id = UserPartition.VERSION_1_SCHEME
        elif value["version"] == UserPartition.VERSION:
            if "scheme" not in value:
                raise TypeError("UserPartition dict {0} missing value key 'scheme'".format(value))
            scheme_id = value["scheme"]
        else:
            raise TypeError("UserPartition dict {0} has unexpected version".format(value))

        groups = [Group.from_json(g) for g in value["groups"]]
        scheme = UserPartition.get_scheme(scheme_id)
        if not scheme:
            raise TypeError("UserPartition dict {0} has unrecognized scheme {1}".format(value, scheme_id))

        return UserPartition(
            value["id"],
            value["name"],
            value["description"],
            groups,
            scheme,
        )

    def get_group(self, group_id):
        """
        Returns the group with the specified id.  Raises NoSuchUserPartitionGroupError if not found.
        """
        # pylint: disable=no-member

        for group in self.groups:
            if group.id == group_id:
                return group

        raise NoSuchUserPartitionGroupError(
            "could not find a Group with ID [{}] in UserPartition [{}]".format(group_id, self.id)
        )
