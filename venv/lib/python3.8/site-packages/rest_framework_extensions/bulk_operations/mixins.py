from django.utils.encoding import force_str

from rest_framework import status
from rest_framework.response import Response
from rest_framework_extensions.settings import extensions_api_settings
from rest_framework_extensions import utils


class BulkOperationBaseMixin:
    def is_object_operation(self):
        return bool(self.get_object_lookup_value())

    def get_object_lookup_value(self):
        return self.kwargs.get(getattr(self, 'lookup_url_kwarg', None) or self.lookup_field, None)

    def is_valid_bulk_operation(self):
        if extensions_api_settings.DEFAULT_BULK_OPERATION_HEADER_NAME:
            header_name = utils.prepare_header_name(
                extensions_api_settings.DEFAULT_BULK_OPERATION_HEADER_NAME)
            return bool(self.request.META.get(header_name, None)), {
                'detail': 'Header \'{0}\' should be provided for bulk operation.'.format(
                    extensions_api_settings.DEFAULT_BULK_OPERATION_HEADER_NAME
                )
            }
        else:
            return True, {}


class ListDestroyModelMixin(BulkOperationBaseMixin):
    def delete(self, request, *args, **kwargs):
        if self.is_object_operation():
            return super().destroy(request, *args, **kwargs)
        else:
            return self.destroy_bulk(request, *args, **kwargs)

    def destroy_bulk(self, request, *args, **kwargs):
        is_valid, errors = self.is_valid_bulk_operation()
        if is_valid:
            queryset = self.filter_queryset(self.get_queryset())
            self.pre_delete_bulk(queryset)  # todo: test and document me
            queryset.delete()
            self.post_delete_bulk(queryset)  # todo: test and document me
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    def pre_delete_bulk(self, queryset):
        """
        Placeholder method for calling before deleting an queryset.
        """
        pass

    def post_delete_bulk(self, queryset):
        """
        Placeholder method for calling after deleting an queryset.
        """
        pass


class ListUpdateModelMixin(BulkOperationBaseMixin):
    def patch(self, request, *args, **kwargs):
        if self.is_object_operation():
            return super().partial_update(request, *args, **kwargs)
        else:
            return self.partial_update_bulk(request, *args, **kwargs)

    def partial_update_bulk(self, request, *args, **kwargs):
        is_valid, errors = self.is_valid_bulk_operation()
        if is_valid:
            queryset = self.filter_queryset(self.get_queryset())
            update_bulk_dict = self.get_update_bulk_dict(
                serializer=self.get_serializer_class()(), data=request.data)
            # todo: test and document me
            self.pre_save_bulk(queryset, update_bulk_dict)
            try:
                queryset.update(**update_bulk_dict)
            except ValueError as e:
                errors = {
                    'detail': force_str(e)
                }
                return Response(errors, status=status.HTTP_400_BAD_REQUEST)
            # todo: test and document me
            self.post_save_bulk(queryset, update_bulk_dict)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

    def get_update_bulk_dict(self, serializer, data):
        update_bulk_dict = {}
        for field_name, field in serializer.fields.items():
            if field_name in data and not field.read_only:
                update_bulk_dict[field.source or field_name] = data[field_name]
        return update_bulk_dict

    def pre_save_bulk(self, queryset, update_bulk_dict):
        """
        Placeholder method for calling before deleting an queryset.
        """
        pass

    def post_save_bulk(self, queryset, update_bulk_dict):
        """
        Placeholder method for calling after deleting an queryset.
        """
        pass
