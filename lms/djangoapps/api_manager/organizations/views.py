# pylint: disable=C0103

""" ORGANIZATIONS API VIEWS """
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api_manager.models import Organization
from api_manager.users.serializers import UserSerializer
from api_manager.utils import str2bool
from student.models import CourseEnrollment

from .serializers import OrganizationSerializer


class OrganizationsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the Organization model.
    """
    serializer_class = OrganizationSerializer
    model = Organization

    @action(methods=['get', 'post'])
    def users(self, request, pk):
        """
        Add a User to an Organization
        """
        if request.method == 'GET':
            include_course_counts = request.QUERY_PARAMS.get('include_course_counts', None)
            users = User.objects.filter(organizations=pk)
            response_data = []
            if users:
                for user in users:
                    serializer = UserSerializer(user)
                    user_data = serializer.data
                    if str2bool(include_course_counts):
                        enrollments = CourseEnrollment.enrollments_for_user(user).count()
                        user_data['course_count'] = enrollments
                    response_data.append(user_data)
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            user_id = request.DATA.get('id')
            try:
                user = User.objects.get(id=user_id)
            except ObjectDoesNotExist:
                message = 'User {} does not exist'.format(user_id)
                return Response({"detail": message}, status.HTTP_400_BAD_REQUEST)
            organization = self.get_object()
            organization.users.add(user)
            organization.save()
            return Response({}, status=status.HTTP_201_CREATED)
