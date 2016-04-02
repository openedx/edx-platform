from rest_framework import viewsets
from .models import Microsite
from .serializers import MicrositeSerializer


class MicrositeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Microsite.objects.all()
    serializer_class = MicrositeSerializer
