from django.conf import settings

# Register signal handlers, but only if Datadog reporting has been made active
if settings.FEATURES.get('ENABLE_DATADOG_REPORTING'):
    # pylint: disable=unused-import
    import signals
    import exceptions