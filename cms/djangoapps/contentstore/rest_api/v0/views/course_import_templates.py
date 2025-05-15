import datetime
import uuid

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import permissions, viewsets
from rest_framework.response import Response

from cms.djangoapps.contentstore.models import CourseImportTemplate
from cms.djangoapps.contentstore.rest_api.v0.serializers.course_import_templates import (
    CourseImportTemplateSerializer,
)

User = get_user_model()


class CourseImportTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = CourseImportTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return templates from configured plugin pipeline or database model.
        """
        # Check if the OPEN_EDX_FILTERS_CONFIG is available with the right filter
        filters_config = getattr(settings, "OPEN_EDX_FILTERS_CONFIG", {})
        if "org.edly.templates.fetch.requested.v1" in filters_config:
            try:
                from course_import.filters import CourseTemplateRequested

                templates_result = CourseTemplateRequested.run_filter(
                    source_type="github",
                    source_config="https://raw.githubusercontent.com/awais786/courses/refs/heads/main/edly_courses.json",
                )

                if templates_result and "result" in templates_result:
                    # Convert the pipeline result to a format compatible with the serializer
                    return self._convert_pipeline_result_to_queryset(
                        templates_result["result"]
                    )
            except (ImportError, Exception) as exc:
                pass

        return CourseImportTemplate.objects.all()

    def list(self, request, *args, **kwargs):
        """
        Override the list method to format the response in a way the frontend expects.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(
            {
                "next": None,
                "previous": None,
                "count": len(serializer.data),
                "num_pages": 1,
                "current_page": 1,
                "start": 0,
                "results": serializer.data,
            }
        )

    def _convert_pipeline_result_to_queryset(self, pipeline_results):
        """
        Convert results from the pipeline to a format compatible with the CourseImportTemplate model.
        The pipeline results seem to have a structure like:
        [
            {
                'courses_name': 'Course Name',
                'metadata': {
                    'thumbnail': 'thumbnail_url',
                    'title': 'Course Title',
                    'description': 'Course Description'
                },
                'zip_url': 'course_template_url'
            },
            ...
        ]

        We'll convert this to a list of CourseImportTemplate objects.
        """
        template_objects = []

        # Using the admin user or the first available user as the added_by
        try:
            admin_user = User.objects.filter(is_staff=True).first()
            if not admin_user:
                admin_user = User.objects.first()
        except Exception:
            # If can't get a user, we'll return an empty queryset
            return CourseImportTemplate.objects.none()

        now = datetime.datetime.now()

        for i, course in enumerate(pipeline_results):
            if not course or "metadata" not in course:
                continue

            metadata = course.get("metadata", {})
            template = CourseImportTemplate(
                id=i + 1,
                name=course.get("courses_name", "Unknown Course"),
                description=metadata.get("description", ""),
                course_template=course.get("zip_url", ""),
                added_by=admin_user,
                created_at=now,
            )

            thumbnail_url = metadata.get("thumbnail")
            if thumbnail_url:
                try:
                    response = requests.get(thumbnail_url)
                    if response.status_code == 200:
                        filename = f"{uuid.uuid4()}.jpg"

                        template.thumbnail.save(
                            filename, ContentFile(response.content), save=False
                        )
                except Exception:
                    pass

            template_objects.append(template)
        return template_objects

    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)
