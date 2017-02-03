""" DRF routers. """

from rest_framework import routers


class SimpleRouter(routers.SimpleRouter):
    """ Simple DRF router. """

    # Note (CCB): This is a retrofit of a DRF 2.4 feature onto DRF 2.3. This is, sadly, simpler than
    # updating edx-ora2 to work with DRF 2.4. See https://github.com/tomchristie/django-rest-framework/pull/1333
    # for details on this specific DRF 2.4 feature.
    def get_lookup_regex(self, viewset, lookup_prefix=''):
        """
        Given a viewset, return the portion of URL regex that is used
        to match against a single instance.
        Note that lookup_prefix is not used directly inside REST rest_framework
        itself, but is required in order to nicely support nested router
        implementations, such as drf-nested-routers.
        https://github.com/alanjds/drf-nested-routers
        """
        base_regex = '(?P<{lookup_prefix}{lookup_field}>{lookup_value})'
        lookup_field = getattr(viewset, 'lookup_field', 'pk')
        try:
            lookup_value = viewset.lookup_value_regex
        except AttributeError:
            # Don't consume `.json` style suffixes
            lookup_value = '[^/.]+'
        return base_regex.format(
            lookup_prefix=lookup_prefix,
            lookup_field=lookup_field,
            lookup_value=lookup_value
        )
