from rest_framework.mixins import (CreateModelMixin,DestroyModelMixin,UpdateModelMixin,ListModelMixin,RetrieveModelMixin)
from rest_framework.viewsets import GenericViewSet
from rest_framework.response import Response
from rest_framework import status
from django_restframework.serializers.serializer import SerializerPlug
from django_restframework.paginations.pagination import MyPagination
from rest_framework.views import APIView

"""
1. post create data
"""
class MyCreateModeMixin(CreateModelMixin,GenericViewSet,SerializerPlug):
    authentication_classes = ()
    permission_classes = ()
    msg_create = "创建成功"
    results_display = True # 是否显示序列化信息, 默认显示

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        # serializer.is_valid(raise_exception=True) # Serializer自带的异常处理(不符合我们的需求,需要自定义)
        self.validation_error(serializer=serializer)  # 自定义Serializer异常处理
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        data = serializer.data if self.results_display else None

        return Response({
            "success": True,
            "msg": self.msg_create,
            "results":data
        }, status=status.HTTP_200_OK)

"""
2. delete destroy data
"""
class MyDeleteModelMixin(DestroyModelMixin, GenericViewSet):
    authentication_classes = ()
    permission_classes = ()
    msg_delete = "成功删除"
    lookup_field = "pk" # 主键

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)

        return Response({
            "success": True,
            "msg": self.msg_delete,
            "results": None
        }, status=status.HTTP_204_NO_CONTENT)

"""
3. put update data
"""
class MyUpdateModelMixin(UpdateModelMixin, GenericViewSet,SerializerPlug):
    authentication_classes = ()
    permission_classes = ()
    msg_update = "修改成功"
    lookup_field = "pk" # 主键
    results_display = True

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        # serializer.is_valid(raise_exception=True)
        self.validation_error(serializer=serializer)  # 自定义Serializer异常处理
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        data = serializer.data if self.results_display else None


        return Response({
            "success": True,
            "msg": self.msg_update,
            "results": data
        }, status=status.HTTP_200_OK)

"""
4. get list data
"""
class MyListModeMixin(ListModelMixin,GenericViewSet):
    authentication_classes = ()
    permission_classes = ()
    pagination_class = MyPagination # 分页
    msg_list = "成功获取列表数据"

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)

        return Response({
            "success": True,
            "msg": self.msg_list,
            "results":serializer.data
        }, status=status.HTTP_200_OK)

"""
5. get retrieve data
"""
class MyRetrieveModelMixin(RetrieveModelMixin,GenericViewSet):
    authentication_classes = ()
    permission_classes = ()
    msg_detail = "成功获取详细数据"
    lookup_field = "pk" # 主键

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        return Response({
            "success": True,
            "msg": self.msg_detail,
            "results":serializer.data
        }, status=status.HTTP_200_OK)

"""
5. APIView
"""
class MyAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()

