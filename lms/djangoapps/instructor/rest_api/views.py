from rest_framework import generics, status
from rest_framework.response import Response

from . import serializers


from .. import permissions

class GetProblemResponseViewset(generics.GenericAPIView):
    serializer_class = serializers.ProblemResponseRequestSerializer
    permission_classes = (
          permissions.CAN_RESEARCH,
    )
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        course_id = kwargs.get('course_id')
        if not course_id:
            return Response({"error": "Course ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            
            # Access validated data with serializer.validated_data
            return Response(status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
        