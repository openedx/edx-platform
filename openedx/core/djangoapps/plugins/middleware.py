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
        slot_namespace = view_func.__qualname__
        if hasattr(view_func, 'get_slot_namespace'):
            assert callable(view_func.get_slot_namespace)
            slot_namespace = view_func.get_slot_namespace()
        elif hasattr(view_func, 'slot_namespace'):
            assert isinstance(view_func.slot_namespace, str)
            slot_namespace = view_func.slot_namespace
        request.slot_namespace = slot_namespace
