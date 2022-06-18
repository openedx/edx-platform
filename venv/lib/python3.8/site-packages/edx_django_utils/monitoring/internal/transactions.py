"""
This is a collection of transaction-related monitoring utilities.

Usage:

    from edx_django_utils.monitoring import ignore_transaction
    ...
    # called from inside a view you want ignored
    ignore_transaction()

Please remember to expose any new methods in the `__init__.py` file.
"""

from contextlib import contextmanager

try:
    import newrelic.agent
except ImportError:
    newrelic = None  # pylint: disable=invalid-name


def set_monitoring_transaction_name(name, group=None, priority=None):
    """
    Sets the transaction name for monitoring.

    This is not cached, and only support reporting to New Relic.

    """
    if newrelic:  # pragma: no cover
        newrelic.agent.set_transaction_name(name, group, priority)


def ignore_transaction():
    """
    Ignore the transaction in monitoring

    This allows us to ignore code paths that are unhelpful to include, such as
    `/health/` checks.
    """
    if newrelic:  # pragma: no cover
        newrelic.agent.ignore_transaction()


@contextmanager
def function_trace(function_name):
    """
    Wraps a chunk of code that we want to appear as a separate, explicit,
    segment in our monitoring tools.
    """
    # Not covering this because if we mock it, we're not really testing anything
    # anyway. If something did break, it should show up in tests for apps that
    # use this code with newrelic enabled, on whatever version of newrelic they
    # run.
    if newrelic:  # pragma: no cover
        if newrelic.version_info[0] >= 5:
            with newrelic.agent.FunctionTrace(function_name):
                yield
        else:
            nr_transaction = newrelic.agent.current_transaction()
            with newrelic.agent.FunctionTrace(nr_transaction, function_name):
                yield
    else:
        yield


class MonitoringTransaction():
    """
    Represents a monitoring transaction (likely the current transaction).
    """
    def __init__(self, transaction):
        self.transaction = transaction

    @property
    def name(self):
        """
        The name of the transaction.

        For NewRelic, the name may look like:
            openedx.core.djangoapps.contentserver.middleware:StaticContentServer

        """
        if self.transaction and hasattr(self.transaction, 'name'):
            return self.transaction.name
        return None


def get_current_transaction():
    """
    Returns the current transaction.
    """
    current_transaction = None
    if newrelic:
        current_transaction = newrelic.agent.current_transaction()

    return MonitoringTransaction(current_transaction)
