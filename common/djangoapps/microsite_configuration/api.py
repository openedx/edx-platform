from django.core.files.storage import DefaultStorage
from rest_framework import views, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import Microsite
from .serializers import MicrositeSerializer, MicrositeListSerializer


class MicrositeViewSet(viewsets.ModelViewSet):
    queryset = Microsite.objects.all()
    serializer_class = MicrositeSerializer
    list_serializer_class = MicrositeListSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            if hasattr(self, 'list_serializer_class'):
                return self.list_serializer_class

        return super(MicrositeViewSet, self).get_serializer_class()


class FileUploadView(views.APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, microsite_id, format=None):
        file_obj = request.data['file']
        field_name = request.data['field_name']
        microsite = Microsite.objects.get(id=microsite_id)
        file_path = self.handle_uploaded_file(file_obj, request.GET.get('filename'))
        microsite.values[field_name] = file_path
        microsite.save()
        return Response({'file_path': file_path}, status=201)

    def handle_uploaded_file(self, content, filename):
        storage = DefaultStorage()
        name = storage.save(filename, content)
        return storage.url(name)
