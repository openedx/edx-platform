"""
API v0 views.
"""

from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from cms.djangoapps.course_to_library_import.api import import_library_from_staged_content
from .serializers import ImportBlocksSerializer


class ImportBlocksView(APIView):
    """
    Import blocks from a course to a library.
    """

    permission_classes = (IsAdminUser,)
    serializer_class = ImportBlocksSerializer

    def post(self, request, *args, **kwargs):
        """
        Import blocks from a course to a library.

        API endpoint: POST /api/v0/course-to-library-import/

        Request:
        {
            "library_key": "lib:org:code:run",
            "course_id": "course-v1:org+course+run",
            "usage_ids": ["block-v1:org+course+run+type@problem+block@12345"],
            "import_id": "78df3b2c-4e5a-4d6b-8c7e-1f2a3b4c5d6e",
            "composition_level": "xblock",
            "override": false
        }

        Response:
        {
            "status": "success"
        }
        """
        data = self.serializer_class(data=request.data)
        data.is_valid(raise_exception=True)

        import_library_from_staged_content(
            library_key=data.validated_data['library_key'],
            user_id=request.user.pk,
            usage_ids=data.validated_data['usage_ids'],
            course_id=data.validated_data['course_id'],
            import_id=data.validated_data['import_id'],
            composition_level=data.validated_data['composition_level'],
            override=data.validated_data['override'],
        )
        return Response({'status': 'success'})
