from django.utils.deprecation import MiddlewareMixin


class ViewNameAndSlotMiddleware(MiddlewareMixin):
    """
    Django middleware object to inject view name into request context
    """
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Injects the view name value into the request context
        """
        request.view_name = view_func.__name__
        # For class-based views the view function will have a `view_class` attribute
        # and we can get the slot_namespace from that
        view = getattr(view_func, 'view_class', view_func)
        request.slot_namespace = view.__qualname__
        if hasattr(view, 'slot_namespace'):
            assert isinstance(view.slot_namespace, str)
            request.slot_namespace = view.slot_namespace
