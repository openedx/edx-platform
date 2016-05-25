from django.core.files.storage import DefaultStorage
from rest_framework import views, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from .models import Microsite
from .serializers import MicrositeSerializer


class MicrositeViewSet(viewsets.ModelViewSet):
    queryset = Microsite.objects.all()
    serializer_class = MicrositeSerializer


class FileUploadView(views.APIView):
    parser_classes = (MultiPartParser,)

    def post(self, request, microsite_id, format=None):
        file_obj = request.data['file']
        field_name = request.data['field_name']
        microsite = Microsite.objects.get(id=microsite_id)
        microsite.values[field_name] = self.handle_uploaded_file(file_obj, request.GET.get('filename'))
        microsite.save()
        return Response(status=204)

    def handle_uploaded_file(self, content, filename):
        storage = DefaultStorage()
        name = storage.save(filename, content)
        return storage.url(name)
