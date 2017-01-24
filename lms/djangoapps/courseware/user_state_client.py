"""
An implementation of :class:`XBlockUserStateClient`, which stores XBlock Scope.user_state
data in a Django ORM model.
"""

import itertools
from operator import attrgetter
from time import time
import logging
try:
    import simplejson as json
except ImportError:
    import json

import newrelic_custom_metrics
import dogstats_wrapper as dog_stats_api
from django.contrib.auth.models import User
from django.db import transaction
from django.db.utils import IntegrityError
from xblock.fields import Scope
from courseware.models import StudentModule, BaseStudentModuleHistory
from edx_user_state_client.interface import XBlockUserStateClient, XBlockUserState

log = logging.getLogger(__name__)


class DjangoXBlockUserStateClient(XBlockUserStateClient):
    """
    An interface that uses the Django ORM StudentModule as a backend.

    A note on the format of state storage:
        The state for an xblock is stored as a serialized JSON dictionary. The model
        field that it is stored in can also take on a value of ``None``. To preserve
        existing analytic uses, we will preserve the following semantics:

        A state of ``None`` means that the user hasn't ever looked at the xblock.
        A state of ``"{}"`` means that the XBlock has at some point stored state for
           the current user, but that that state has been deleted.
        Otherwise, the dictionary contains all data stored for the user.

        None of these conditions should violate the semantics imposed by
        XBlockUserStateClient (for instance, once all fields have been deleted from
        an XBlock for a user, the state will be listed as ``None`` by :meth:`get_history`,
        even though the actual stored state in the database will be ``"{}"``).
    """

    # Use this sample rate for DataDog events.
    API_DATADOG_SAMPLE_RATE = 0.1

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

    def __init__(self, user=None):
        """
        Arguments:
            user (:class:`~User`): An already-loaded django user. If this user matches the username
                supplied to `set_many`, then that will reduce the number of queries made to store
                the user state.
        """
        self.user = user

    def _get_student_modules(self, username, block_keys):
        """
        Retrieve the :class:`~StudentModule`s for the supplied ``username`` and ``block_keys``.

        Arguments:
            username (str): The name of the user to load `StudentModule`s for.
            block_keys (list of :class:`~UsageKey`): The set of XBlocks to load data for.
        """
        course_key_func = attrgetter('course_key')
        by_course = itertools.groupby(
            sorted(block_keys, key=course_key_func),
            course_key_func,
        )

        for course_key, usage_keys in by_course:
            query = StudentModule.objects.chunked_filter(
                'module_state_key__in',
                usage_keys,
                student__username=username,
                course_id=course_key,
            )

            for student_module in query:
                usage_key = student_module.module_state_key.map_into_course(student_module.course_id)
                yield (student_module, usage_key)

    def _ddog_increment(self, evt_time, evt_name):
        """
        DataDog increment method.
        """
        dog_stats_api.increment(
            'DjangoXBlockUserStateClient.{}'.format(evt_name),
            timestamp=evt_time,
            sample_rate=self.API_DATADOG_SAMPLE_RATE,
        )

    def _ddog_histogram(self, evt_time, evt_name, value):
        """
        DataDog histogram method.
        """
        dog_stats_api.histogram(
            'DjangoXBlockUserStateClient.{}'.format(evt_name),
            value,
            timestamp=evt_time,
            sample_rate=self.API_DATADOG_SAMPLE_RATE,
        )

    def _nr_metric_name(self, function_name, stat_name, block_type=None):
        """
        Return a metric name (string) representing the provided descriptors.
        The return value is directly usable for custom NR metrics.
        """
        if block_type is None:
            metric_name_parts = ['xb_user_state', function_name, stat_name]
        else:
            metric_name_parts = ['xb_user_state', function_name, block_type, stat_name]
        return '.'.join(metric_name_parts)

    def _nr_stat_accumulate(self, function_name, stat_name, value):
        """
        Accumulate arbitrary NR stats (not specific to block types).
        """
        newrelic_custom_metrics.accumulate(
            self._nr_metric_name(function_name, stat_name),
            value
        )

    def _nr_stat_increment(self, function_name, stat_name, count=1):
        """
        Increment arbitrary NR stats (not specific to block types).
        """
        self._nr_stat_accumulate(function_name, stat_name, count)

    def _nr_block_stat_accumulate(self, function_name, block_type, stat_name, value):
        """
        Accumulate NR stats related to block types.
        """
        newrelic_custom_metrics.accumulate(
            self._nr_metric_name(function_name, stat_name),
            value,
        )
        newrelic_custom_metrics.accumulate(
            self._nr_metric_name(function_name, stat_name, block_type=block_type),
            value,
        )

    def _nr_block_stat_increment(self, function_name, block_type, stat_name, count=1):
        """
        Increment NR stats related to block types.
        """
        self._nr_block_stat_accumulate(function_name, block_type, stat_name, count)

    def get_many(self, username, block_keys, scope=Scope.user_state, fields=None):
        """
        Retrieve the stored XBlock state for the specified XBlock usages.

        Arguments:
            username: The name of the user whose state should be retrieved
            block_keys ([UsageKey]): A list of UsageKeys identifying which xblock states to load.
            scope (Scope): The scope to load data from
            fields: A list of field values to retrieve. If None, retrieve all stored fields.

        Yields:
            XBlockUserState tuples for each specified UsageKey in block_keys.
            field_state is a dict mapping field names to values.
        """
        if scope != Scope.user_state:
            raise ValueError("Only Scope.user_state is supported, not {}".format(scope))

        total_block_count = 0
        evt_time = time()

        # count how many times this function gets called
        self._nr_stat_increment('get_many', 'calls')

        # keep track of blocks requested
        self._ddog_histogram(evt_time, 'get_many.blks_requested', len(block_keys))
        self._nr_stat_accumulate('get_many', 'blocks_requested', len(block_keys))

        modules = self._get_student_modules(username, block_keys)
        for module, usage_key in modules:
            if module.state is None:
                self._ddog_increment(evt_time, 'get_many.empty_state')
                continue

            state = json.loads(module.state)
            state_length = len(module.state)

            # record this metric before the check for empty state, so that we
            # have some visibility into empty blocks.
            self._ddog_histogram(evt_time, 'get_many.block_size', state_length)

            # If the state is the empty dict, then it has been deleted, and so
            # conformant UserStateClients should treat it as if it doesn't exist.
            if state == {}:
                continue

            # collect statistics for metric reporting
            self._nr_block_stat_increment('get_many', usage_key.block_type, 'blocks_out')
            self._nr_block_stat_accumulate('get_many', usage_key.block_type, 'size', state_length)
            total_block_count += 1

            # filter state on fields
            if fields is not None:
                state = {
                    field: state[field]
                    for field in fields
                    if field in state
                }
            yield XBlockUserState(username, usage_key, state, module.modified, scope)

        # The rest of this method exists only to report metrics.
        finish_time = time()
        duration = (finish_time - evt_time) * 1000  # milliseconds

        self._ddog_histogram(evt_time, 'get_many.blks_out', total_block_count)
        self._ddog_histogram(evt_time, 'get_many.response_time', duration)
        self._nr_stat_accumulate('get_many', 'duration', duration)

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
        if scope != Scope.user_state:
            raise ValueError("Only Scope.user_state is supported")

        # count how many times this function gets called
        self._nr_stat_increment('set_many', 'calls')

        # We do a find_or_create for every block (rather than re-using field objects
        # that were queried in get_many) so that if the score has
        # been changed by some other piece of the code, we don't overwrite
        # that score.
        if self.user is not None and self.user.username == username:
            user = self.user
        else:
            user = User.objects.get(username=username)

        if user.is_anonymous():
            # Anonymous users cannot be persisted to the database, so let's just use
            # what we have.
            return

        evt_time = time()

        for usage_key, state in block_keys_to_state.items():
            student_module, created = StudentModule.objects.get_or_create(
                student=user,
                course_id=usage_key.course_key,
                module_state_key=usage_key,
                defaults={
                    'state': json.dumps(state),
                    'module_type': usage_key.block_type,
                },
            )

            num_fields_before = num_fields_after = num_new_fields_set = len(state)
            num_fields_updated = 0
            if not created:
                if student_module.state is None:
                    current_state = {}
                else:
                    current_state = json.loads(student_module.state)
                num_fields_before = len(current_state)
                current_state.update(state)
                num_fields_after = len(current_state)
                student_module.state = json.dumps(current_state)
                try:
                    with transaction.atomic():
                        # Updating the object - force_update guarantees no INSERT will occur.
                        student_module.save(force_update=True)
                except IntegrityError:
                    # The UPDATE above failed. Log information - but ignore the error.
                    # See https://openedx.atlassian.net/browse/TNL-5365
                    log.warning("set_many: IntegrityError for student {} - course_id {} - usage key {}".format(
                        user, repr(unicode(usage_key.course_key)), usage_key
                    ))
                    log.warning("set_many: All {} block keys: {}".format(
                        len(block_keys_to_state), block_keys_to_state.keys()
                    ))

            # DataDog and New Relic reporting

            # record the size of state modifications
            self._nr_block_stat_accumulate('set_many', usage_key.block_type, 'size', len(student_module.state))

            # Record whether a state row has been created or updated.
            if created:
                self._ddog_increment(evt_time, 'set_many.state_created')
                self._nr_block_stat_increment('set_many', usage_key.block_type, 'blocks_created')
            else:
                self._ddog_increment(evt_time, 'set_many.state_updated')
                self._nr_block_stat_increment('set_many', usage_key.block_type, 'blocks_updated')

            # Event to record number of fields sent in to set/set_many.
            self._ddog_histogram(evt_time, 'set_many.fields_in', len(state))

            # Event to record number of new fields set in set/set_many.
            num_new_fields_set = num_fields_after - num_fields_before
            self._ddog_histogram(evt_time, 'set_many.fields_set', num_new_fields_set)

            # Event to record number of existing fields updated in set/set_many.
            num_fields_updated = max(0, len(state) - num_new_fields_set)
            self._ddog_histogram(evt_time, 'set_many.fields_updated', num_fields_updated)

        # Events for the entire set_many call.
        finish_time = time()
        duration = (finish_time - evt_time) * 1000  # milliseconds
        self._ddog_histogram(evt_time, 'set_many.blks_updated', len(block_keys_to_state))
        self._ddog_histogram(evt_time, 'set_many.response_time', duration)
        self._nr_stat_accumulate('set_many', 'duration', duration)

    def delete_many(self, username, block_keys, scope=Scope.user_state, fields=None):
        """
        Delete the stored XBlock state for a many xblock usages.

        Arguments:
            username: The name of the user whose state should be deleted
            block_keys (list): The UsageKey identifying which xblock state to delete.
            scope (Scope): The scope to delete data from
            fields: A list of fields to delete. If None, delete all stored fields.
        """
        if scope != Scope.user_state:
            raise ValueError("Only Scope.user_state is supported")

        evt_time = time()
        if fields is None:
            self._ddog_increment(evt_time, 'delete_many.empty_state')
        else:
            self._ddog_histogram(evt_time, 'delete_many.field_count', len(fields))

        self._ddog_histogram(evt_time, 'delete_many.block_count', len(block_keys))

        student_modules = self._get_student_modules(username, block_keys)
        for student_module, _ in student_modules:
            if fields is None:
                student_module.state = "{}"
            else:
                current_state = json.loads(student_module.state)
                for field in fields:
                    if field in current_state:
                        del current_state[field]

                student_module.state = json.dumps(current_state)

            # We just read this object, so we know that we can do an update
            student_module.save(force_update=True)

        # Event for the entire delete_many call.
        finish_time = time()
        self._ddog_histogram(evt_time, 'delete_many.response_time', (finish_time - evt_time) * 1000)

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

        if scope != Scope.user_state:
            raise ValueError("Only Scope.user_state is supported")
        student_modules = list(
            student_module
            for student_module, usage_id
            in self._get_student_modules(username, [block_key])
        )
        if len(student_modules) == 0:
            raise self.DoesNotExist()

        history_entries = BaseStudentModuleHistory.get_history(student_modules)

        # If no history records exist, raise an error
        if not history_entries:
            raise self.DoesNotExist()

        for history_entry in history_entries:
            state = history_entry.state

            # If the state is serialized json, then load it
            if state is not None:
                state = json.loads(state)

            # If the state is empty, then for the purposes of `get_history`, it has been
            # deleted, and so we list that entry as `None`.
            if state == {}:
                state = None

            block_key = history_entry.csm.module_state_key
            block_key = block_key.map_into_course(
                history_entry.csm.course_id
            )

            yield XBlockUserState(username, block_key, state, history_entry.created, scope)

    def iter_all_for_block(self, block_key, scope=Scope.user_state, batch_size=None):
        """
        You get no ordering guarantees. Fetching will happen in batch_size
        increments. If you're using this method, you should be running in an
        async task.
        """
        if scope != Scope.user_state:
            raise ValueError("Only Scope.user_state is supported")
        raise NotImplementedError()

    def iter_all_for_course(self, course_key, block_type=None, scope=Scope.user_state, batch_size=None):
        """
        You get no ordering guarantees. Fetching will happen in batch_size
        increments. If you're using this method, you should be running in an
        async task.
        """
        if scope != Scope.user_state:
            raise ValueError("Only Scope.user_state is supported")
        raise NotImplementedError()
