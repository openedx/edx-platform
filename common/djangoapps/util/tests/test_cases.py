from django.conf import settings

from db_utils import transaction


def disable_transaction_methods():
    """
    Helper method to path transaction decorator
    'commit_on_success_with_read_committed'
    """

    def dummy_commit_on_success():
        def decorator(func):
            return func
        return decorator

    if not settings.FEATURES.get('CHANGE_TRANSACTION_LEVEL', True):
        transaction.commit_on_success_with_read_committed = dummy_commit_on_success