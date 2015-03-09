"""
A baseclass for a generic client for accessing XBlock Scope.user_state field data.
"""

from abc import abstractmethod

from contracts import contract, new_contract, ContractsMeta
from opaque_keys.edx.keys import UsageKey
from xblock.fields import Scope, ScopeBase

new_contract('UsageKey', UsageKey)

class XBlockUserStateClient(object):
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

    Open Questions:
    1. Is it sufficient to just send the block_key in and extract course +
       version info from it?
    2. Do we want to use the username as the identifier? Privacy implications?
       Ease of debugging?
    3. Would a get_many_by_type() be useful?
    """

    __metaclass__ = ContractsMeta

    class ServiceUnavailable(Exception):
        """
        This error is raised if the service backing this client is currently unavailable.
        """
        pass

    class PermissionDenied(Exception):
        """
        This error is raised if the caller is not allowed to access the requested data.
        """
        pass

    class DoesNotExist(Exception):
        """
        This error is raised if the caller has requested data that does not exist.
        """
        pass

    @contract(
        username="basestring",
        block_key=UsageKey,
        scope=ScopeBase,
        fields="seq(basestring)|set(basestring)|None",
        returns="dict(basestring: *)"
    )
    def get(self, username, block_key, scope=Scope.user_state, fields=None):
        """
        Retrieve the stored XBlock state for a single xblock usage.

        Arguments:
            username: The name of the user whose state should be retrieved
            block_key (UsageKey): The UsageKey identifying which xblock state to load.
            scope (Scope): The scope to load data from
            fields: A list of field values to retrieve. If None, retrieve all stored fields.

        Returns
            dict: A dictionary mapping field names to values
        """
        return next(self.get_many(username, [block_key], scope, fields=fields))[1]

    @contract(
        username="basestring",
        block_key=UsageKey,
        state="dict(basestring: *)",
        scope=ScopeBase,
        returns=None,
    )
    def set(self, username, block_key, state, scope=Scope.user_state):
        """
        Set fields for a particular XBlock.

        Arguments:
            username: The name of the user whose state should be retrieved
            block_key (UsageKey): The UsageKey identifying which xblock state to load.
            state (dict): A dictionary mapping field names to values
            scope (Scope): The scope to store data to
        """
        self.set_many(username, {block_key: state}, scope)

    @contract(
        username="basestring",
        block_key=UsageKey,
        scope=ScopeBase,
        fields="seq(basestring)|set(basestring)|None",
        returns=None,
    )
    def delete(self, username, block_key, scope=Scope.user_state, fields=None):
        """
        Delete the stored XBlock state for a single xblock usage.

        Arguments:
            username: The name of the user whose state should be deleted
            block_key (UsageKey): The UsageKey identifying which xblock state to delete.
            scope (Scope): The scope to delete data from
            fields: A list of fields to delete. If None, delete all stored fields.
        """
        return self.delete_many(username, [block_key], scope, fields=fields)

    @contract(
        username="basestring",
        block_key=UsageKey,
        scope=ScopeBase,
        fields="seq(basestring)|set(basestring)|None",
        returns="dict(basestring: datetime)",
    )
    def get_mod_date(self, username, block_key, scope=Scope.user_state, fields=None):
        """
        Get the last modification date for fields from the specified blocks.

        Arguments:
            username: The name of the user whose state should queried
            block_key (UsageKey): The UsageKey identifying which xblock modification dates to retrieve.
            scope (Scope): The scope to retrieve from.
            fields: A list of fields to query. If None, query all fields.
                Specific implementations are free to return the same modification date
                for all fields, if they don't store changes individually per field.
                Implementations may omit fields for which data has not been stored.

        Returns: list a dict of {field_name: modified_date} for each selected field.
        """
        results = self.get_mod_date_many(username, [block_key], scope, fields=fields)
        return {
            field: date for (_, field, date) in results
        }

    @contract(
        username="basestring",
        block_keys="seq(UsageKey)|set(UsageKey)",
        scope=ScopeBase,
        fields="seq(basestring)|set(basestring)|None",
    )
    @abstractmethod
    def get_many(self, username, block_keys, scope=Scope.user_state, fields=None):
        """
        Retrieve the stored XBlock state for a single xblock usage.

        Arguments:
            username: The name of the user whose state should be retrieved
            block_keys ([UsageKey]): A list of UsageKeys identifying which xblock states to load.
            scope (Scope): The scope to load data from
            fields: A list of field values to retrieve. If None, retrieve all stored fields.

        Yields:
            (UsageKey, field_state) tuples for each specified UsageKey in block_keys.
            field_state is a dict mapping field names to values.
        """
        raise NotImplementedError()

    @contract(
        username="basestring",
        block_keys_to_state="dict(UsageKey: dict(basestring: *))",
        scope=ScopeBase,
        returns=None,
    )
    @abstractmethod
    def set_many(self, username, block_keys_to_state, scope=Scope.user_state):
        """
        Set fields for a particular XBlock.

        Arguments:
            username: The name of the user whose state should be retrieved
            block_keys_to_state (dict): A dict mapping UsageKeys to state dicts.
                Each state dict maps field names to values. These state dicts
                are overlaid over the stored state. To delete fields, use
                :meth:`delete` or :meth:`delete_many`.
            scope (Scope): The scope to load data from
        """
        raise NotImplementedError()

    @contract(
        username="basestring",
        block_keys="seq(UsageKey)|set(UsageKey)",
        scope=ScopeBase,
        fields="seq(basestring)|set(basestring)|None",
        returns=None,
    )
    @abstractmethod
    def delete_many(self, username, block_keys, scope=Scope.user_state, fields=None):
        """
        Delete the stored XBlock state for a many xblock usages.

        Arguments:
            username: The name of the user whose state should be deleted
            block_key (UsageKey): The UsageKey identifying which xblock state to delete.
            scope (Scope): The scope to delete data from
            fields: A list of fields to delete. If None, delete all stored fields.
        """
        raise NotImplementedError()

    @contract(
        username="basestring",
        block_keys="seq(UsageKey)|set(UsageKey)",
        scope=ScopeBase,
        fields="seq(basestring)|set(basestring)|None",
    )
    @abstractmethod
    def get_mod_date_many(self, username, block_keys, scope=Scope.user_state, fields=None):
        """
        Get the last modification date for fields from the specified blocks.

        Arguments:
            username: The name of the user whose state should be queried
            block_key (UsageKey): The UsageKey identifying which xblock modification dates to retrieve.
            scope (Scope): The scope to retrieve from.
            fields: A list of fields to query. If None, delete all stored fields.
                Specific implementations are free to return the same modification date
                for all fields, if they don't store changes individually per field.
                Implementations may omit fields for which data has not been stored.

        Yields: tuples of (block, field_name, modified_date) for each selected field.
        """
        raise NotImplementedError()

    def get_history(self, username, block_key, scope=Scope.user_state):
        """We don't guarantee that history for many blocks will be fast."""
        raise NotImplementedError()

    def iter_all_for_block(self, block_key, scope=Scope.user_state, batch_size=None):
        """
        You get no ordering guarantees. Fetching will happen in batch_size
        increments. If you're using this method, you should be running in an
        async task.
        """
        raise NotImplementedError()

    def iter_all_for_course(self, course_key, block_type=None, scope=Scope.user_state, batch_size=None):
        """
        You get no ordering guarantees. Fetching will happen in batch_size
        increments. If you're using this method, you should be running in an
        async task.
        """
        raise NotImplementedError()
