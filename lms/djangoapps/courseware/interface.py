"""
A baseclass for a generic client for accessing XBlock Scope.user_state field data.
"""

from abc import abstractmethod
from collections import namedtuple

from xblock.fields import Scope


class XBlockUserState(namedtuple('_XBlockUserState', ['username', 'block_key', 'state', 'updated', 'scope'])):
    """
    The current state of a single XBlock.

    Arguments:
        username: The username of the user that stored this state.
        block_key: The key identifying the scoped state. Depending on the :class:`~xblock.fields.BlockScope` of

                  ``scope``, this may take one of several types:

                      * ``USAGE``: :class:`~opaque_keys.edx.keys.UsageKey`
                      * ``DEFINITION``: :class:`~opaque_keys.edx.keys.DefinitionKey`
                      * ``TYPE``: :class:`str`
                      * ``ALL``: ``None``
        state: A dict mapping field names to the values of those fields for this XBlock.
        updated: A :class:`datetime.datetime`. We guarantee that the fields
                 that were returned in "state" have not been changed since
                 this time (in UTC).
        scope: A :class:`xblock.fields.Scope` identifying which XBlock scope this state is coming from.
    """
    __slots__ = ()

    def __repr__(self):
        return "{}{!r}".format(  # pylint: disable=consider-using-f-string
            self.__class__.__name__,
            tuple(self)
        )


class XBlockUserStateClient():
    """
    First stab at an interface for accessing XBlock User State. This will have
    use StudentModule as a backing store in the default case.

    Scope/Goals:

        1. Mediate access to all student-specific state stored by XBlocks.
            a. This includes "preferences" and "user_info" (i.e. UserScope.ONE)
            b. This includes XBlock Asides.
            c. This may later include user_state_summary (i.e. UserScope.ALL).
            d. This may include group state in the future.
            e. This may include other key types + UserScope.ONE (e.g. Definition)
        2. Assume network service semantics.
            At some point, this will probably be calling out to an external service.
            Even if it doesn't, we want to be able to implement circuit breakers, so
            that a failure in StudentModule doesn't bring down the whole site.
            This also implies that the client is running as a user, and whatever is
            backing it is smart enough to do authorization checks.
        3. This does not yet cover export-related functionality.
    """

    class ServiceUnavailable(Exception):
        """
        This error is raised if the service backing this client is currently unavailable.
        """

    class PermissionDenied(Exception):
        """
        This error is raised if the caller is not allowed to access the requested data.
        """

    class DoesNotExist(Exception):
        """
        This error is raised if the caller has requested data that does not exist.
        """

    def get(self, username, block_key, scope=Scope.user_state, fields=None):
        """
        Retrieve the stored XBlock state for a single xblock usage.

        Arguments:
            username: The name of the user whose state should be retrieved
            block_key: The key identifying which xblock state to load.
            scope (Scope): The scope to load data from
            fields: A list of field values to retrieve. If None, retrieve all stored fields.

        Returns:
            XBlockUserState: The current state of the block for the specified username and block_key.

        Raises:
            DoesNotExist if no entry is found.
        """
        try:
            return next(self.get_many(username, [block_key], scope, fields=fields))
        except StopIteration as exception:
            raise self.DoesNotExist() from exception

    def set(self, username, block_key, state, scope=Scope.user_state):
        """
        Set fields for a particular XBlock.

        Arguments:
            username: The name of the user whose state should be retrieved
            block_key: The key identifying which xblock state to load.
            state (dict): A dictionary mapping field names to values
            scope (Scope): The scope to store data to
        """
        self.set_many(username, {block_key: state}, scope)

    def delete(self, username, block_key, scope=Scope.user_state, fields=None):
        """
        Delete the stored XBlock state for a single xblock usage.

        Arguments:
            username: The name of the user whose state should be deleted
            block_key: The key identifying which xblock state to delete.
            scope (Scope): The scope to delete data from
            fields: A list of fields to delete. If None, delete all stored fields.
        """
        return self.delete_many(username, [block_key], scope, fields=fields)

    @abstractmethod
    def get_many(self, username, block_keys, scope=Scope.user_state, fields=None):
        """
        Retrieve the stored XBlock state for a single xblock usage.

        Arguments:
            username: The name of the user whose state should be retrieved
            block_keys: A list of keys identifying which xblock states to load.
            scope (Scope): The scope to load data from
            fields: A list of field values to retrieve. If None, retrieve all stored fields.

        Yields:
            XBlockUserState tuples for each specified key in block_keys.
            field_state is a dict mapping field names to values.
        """
        raise NotImplementedError()

    @abstractmethod
    def set_many(self, username, block_keys_to_state, scope=Scope.user_state):
        """
        Set fields for a particular XBlock.

        Arguments:
            username: The name of the user whose state should be retrieved
            block_keys_to_state (dict): A dict mapping keys to state dicts.
                Each state dict maps field names to values. These state dicts
                are overlaid over the stored state. To delete fields, use
                :meth:`delete` or :meth:`delete_many`.
            scope (Scope): The scope to load data from
        """
        raise NotImplementedError()

    @abstractmethod
    def delete_many(self, username, block_keys, scope=Scope.user_state, fields=None):
        """
        Delete the stored XBlock state for a many xblock usages.

        Arguments:
            username: The name of the user whose state should be deleted
            block_key: The key identifying which xblock state to delete.
            scope (Scope): The scope to delete data from
            fields: A list of fields to delete. If None, delete all stored fields.
        """
        raise NotImplementedError()

    def get_history(self, username, block_key, scope=Scope.user_state):
        """
        Retrieve history of state changes for a given block for a given
        student.  We don't guarantee that history for many blocks will be fast.

        If the specified block doesn't exist, raise :class:`~DoesNotExist`.

        Arguments:
            username: The name of the user whose history should be retrieved.
            block_key: The key identifying which xblock history to retrieve.
            scope (Scope): The scope to load data from.

        Yields:
            XBlockUserState entries for each modification to the specified XBlock, from latest
            to earliest.
        """
        raise NotImplementedError()

    def iter_all_for_block(self, block_key, scope=Scope.user_state):
        """
        You get no ordering guarantees. If you're using this method, you should be running in an
        async task.
        """
        raise NotImplementedError()

    def iter_all_for_course(self, course_key, block_type=None, scope=Scope.user_state):
        """
        You get no ordering guarantees. If you're using this method, you should be running in an
        async task.
        """
        raise NotImplementedError()
