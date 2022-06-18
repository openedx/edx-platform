from rest_framework.permissions import DjangoObjectPermissions


class ExtendedDjangoObjectPermissions(DjangoObjectPermissions):
    hide_forbidden_for_read_objects = True

    def has_object_permission(self, request, view, obj):
        if self.hide_forbidden_for_read_objects:
            return super().has_object_permission(request, view, obj)
        else:
            model_cls = getattr(view, 'model', None)
            queryset = getattr(view, 'queryset', None)

            if model_cls is None and queryset is not None:
                model_cls = queryset.model

            perms = self.get_required_object_permissions(
                request.method, model_cls)
            user = request.user

            return user.has_perms(perms, obj)
