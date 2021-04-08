"""
View decorator to add a maintenance banner configured in settings.
"""


from functools import wraps

from django.conf import settings

from openedx.core.djangoapps.util.user_messages import PageLevelMessages
from openedx.core.djangoapps.util.waffle import DISPLAY_MAINTENANCE_WARNING


def add_maintenance_banner(func):
    """
    View decorator to select where exactly the banner will appear

    Add to function-based views like this:

        from openedx.core.djangoapps.util.maintenance_banner import add_maintenance_banner

        @add_maintenance_banner
        def my_view(request):
            ...

    Add to class-based views using method_decorator:

        from openedx.core.djangoapps.util.maintenance_banner import add_maintenance_banner
        from django.utils.decorators import method_decorator

        @method_decorator(add_maintenance_banner, name='dispatch')
        class MyView(View):
            ...
    """
    @wraps(func)
    def _decorated(request, *args, **kwargs):  # pylint: disable=missing-docstring
        if DISPLAY_MAINTENANCE_WARNING.is_enabled():
            if hasattr(settings, 'MAINTENANCE_BANNER_TEXT') and settings.MAINTENANCE_BANNER_TEXT:
                # The waffle switch is enabled and the banner text is defined
                # and non-empty.  We can now register the message:
                PageLevelMessages.register_warning_message(request, settings.MAINTENANCE_BANNER_TEXT)
        return func(request, *args, **kwargs)
    return _decorated
