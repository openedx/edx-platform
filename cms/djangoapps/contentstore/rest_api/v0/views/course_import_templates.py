from rest_framework import viewsets, permissions

from cms.djangoapps.contentstore.models import CourseImportTemplate
from cms.djangoapps.contentstore.rest_api.v0.serializers.course_import_templates import CourseImportTemplateSerializer


class CourseImportTemplateViewSet(viewsets.ModelViewSet):
    queryset = CourseImportTemplate.objects.all()
    serializer_class = CourseImportTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)
