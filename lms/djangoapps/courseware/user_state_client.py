"""
An implementation of :class:`XBlockUserStateClient`, which stores XBlock Scope.user_state
data in a Django ORM model.
"""

from xblock_user_state.interface import DjangoXBlockUserStateClient


class DjangoXBlockUserStateClient(DjangoXBlockUserStateClient):
    """
    An interface that uses the Django ORM StudentModule as a backend.
    """

    class ServiceUnavailable(XBlockUserStateClient.ServiceUnavailable):
        """
        This error is raised if the service backing this client is currently unavailable.
        """
        pass

    class PermissionDenied(XBlockUserStateClient.PermissionDenied):
        """
        This error is raised if the caller is not allowed to access the requested data.
        """
        pass

    class DoesNotExist(XBlockUserStateClient.DoesNotExist):
        """
        This error is raised if the caller has requested data that does not exist.
        """
        pass

    def get(username, block_key, scope=Scope.user_state):
        return self.get_many(username, [block_key], scope)

    def set(username, block_key, state, scope=Scope.user_state):
        self.set_many(username, {block_key: state}, scope)

    def get_many(username, block_keys, scope=Scope.user_state):
        """Returns dict of block_id -> state."""
        raise NotImplementedError()

    def set_many(username, block_keys_to_state, scope=Scope.user_state):
        raise NotImplementedError()

    def get_history(username, block_key, scope=Scope.user_state):
        """We don't guarantee that history for many blocks will be fast."""
        raise NotImplementedError()

    def iter_all_for_block(block_key, scope=Scope.user_state, batch_size=None):
        """
        You get no ordering guarantees. Fetching will happen in batch_size
        increments. If you're using this method, you should be running in an
        async task.
        """
        raise NotImplementedError()

    def iter_all_for_course(course_key, block_type=None, scope=Scope.user_state, batch_size=None):
        """
        You get no ordering guarantees. Fetching will happen in batch_size
        increments. If you're using this method, you should be running in an
        async task.
        """
        raise NotImplementedError()
