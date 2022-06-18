from django.db.backends.base.features import BaseDatabaseFeatures


class DatabaseFeatures(BaseDatabaseFeatures):
    supports_transactions = False
    # djongo doesn't seem to support this currently
    has_bulk_insert = True
    has_native_uuid_field = True
    supports_timezones = False
    uses_savepoints = False
    can_clone_databases = True
    test_db_allows_multiple_connections = False
    supports_unspecified_pk = True

