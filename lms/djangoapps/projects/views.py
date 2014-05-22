# pylint: disable=C0103
# pylint: disable=W0613

""" WORKGROUPS API VIEWS """
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework import status
from rest_framework.response import Response

from .models import Workgroup, Project, Submission
from .models import SubmissionReview, PeerReview
from .serializers import UserSerializer, GroupSerializer
from .serializers import WorkgroupSerializer, ProjectSerializer, SubmissionSerializer
from .serializers import SubmissionReviewSerializer, PeerReviewSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the Group model (auth_group).
    """
    serializer_class = GroupSerializer
    model = Group


class UserViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the User model (auth_user).
    """
    serializer_class = UserSerializer
    model = User


class WorkgroupsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the Workgroup model.
    """
    serializer_class = WorkgroupSerializer
    model = Workgroup

    @action()
    def groups(self, request, pk):
        """
        Add a Group to a Workgroup
        """
        group_id = request.DATA.get('id')
        try:
            group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            message = 'Group {} does not exist'.format(group_id)
            return Response({"detail": message}, status.HTTP_400_BAD_REQUEST)
        workgroup = self.get_object()
        workgroup.groups.add(group)
        workgroup.save()
        return Response({}, status=status.HTTP_201_CREATED)

    @action()
    def users(self, request, pk):
        """
        Add a User to a Workgroup
        """
        user_id = request.DATA.get('id')
        try:
            user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            message = 'User {} does not exist'.format(user_id)
            return Response({"detail": message}, status.HTTP_400_BAD_REQUEST)
        workgroup = self.get_object()
        workgroup.users.add(user)
        workgroup.save()
        return Response({}, status=status.HTTP_201_CREATED)


class ProjectsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the Project model.
    """
    serializer_class = ProjectSerializer
    model = Project

    @action()
    def workgroups(self, request, pk):
        """
        Add a Workgroup to a Project
        """
        workgroup_id = request.DATA.get('id')
        try:
            workgroup = Workgroup.objects.get(id=workgroup_id)
        except ObjectDoesNotExist:
            message = 'Workgroup {} does not exist'.format(workgroup_id)
            return Response({"detail": message}, status.HTTP_400_BAD_REQUEST)
        project = self.get_object()
        project.workgroups.add(workgroup)
        project.save()
        return Response({}, status=status.HTTP_201_CREATED)


class SubmissionsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the Submission model.
    """
    serializer_class = SubmissionSerializer
    model = Submission


class SubmissionReviewsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the SubmissionReview model.
    """
    serializer_class = SubmissionReviewSerializer
    model = SubmissionReview


class PeerReviewsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the PeerReview model.
    """
    serializer_class = PeerReviewSerializer
    model = PeerReview
