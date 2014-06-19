# pylint: disable=C0103
# pylint: disable=W0613

""" WORKGROUPS API VIEWS """
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import viewsets
from rest_framework.decorators import action, link
from rest_framework import status
from rest_framework.response import Response

from xblock.fields import Scope
from xblock.runtime import KeyValueStore

from courseware.courses import get_course
from courseware.model_data import FieldDataCache
from xmodule.modulestore import Location

from .models import Project, Workgroup, WorkgroupSubmission
from .models import WorkgroupReview, WorkgroupSubmissionReview, WorkgroupPeerReview
from .serializers import UserSerializer, GroupSerializer
from .serializers import ProjectSerializer, WorkgroupSerializer, WorkgroupSubmissionSerializer
from .serializers import WorkgroupReviewSerializer, WorkgroupSubmissionReviewSerializer, WorkgroupPeerReviewSerializer


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

    @action(methods=['get', 'post'])
    def groups(self, request, pk):
        """
        Add a Group to a Workgroup
        """
        if request.method == 'GET':
            groups = Group.objects.filter(workgroups=pk)
            response_data = []
            if groups:
                for group in groups:
                    serializer = GroupSerializer(group)
                    response_data.append(serializer.data)
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            group_id = request.DATA.get('id')
            try:
                group = Group.objects.get(id=group_id)
            except ObjectDoesNotExist:
                message = 'Group {} does not exist'.format(group_id)
                return Response({"detail": message}, status.HTTP_400_BAD_REQUEST)
            workgroup = self.get_object()
            workgroup.groups.add(group)
            workgroup.save()
            print workgroup.groups.all()
            return Response({}, status=status.HTTP_201_CREATED)

    @action(methods=['get', 'post', 'delete'])
    def users(self, request, pk):
        """
        Add a User to a Workgroup
        """
        if request.method == 'GET':
            users = User.objects.filter(workgroups=pk)
            response_data = []
            if users:
                for user in users:
                    serializer = UserSerializer(user)
                    response_data.append(serializer.data)
            return Response(response_data, status=status.HTTP_200_OK)
        elif request.method == 'POST':
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
        else:
            user_id = request.DATA.get('id')
            try:
                user = User.objects.get(id=user_id)
            except ObjectDoesNotExist:
                message = 'User {} does not exist'.format(user_id)
                return Response({"detail": message}, status.HTTP_400_BAD_REQUEST)
            workgroup = self.get_object()
            workgroup.users.remove(user)
            return Response({}, status=status.HTTP_204_NO_CONTENT)

    @link()
    def peer_reviews(self, request, pk):
        """
        View Peer Reviews for a specific Workgroup
        """
        peer_reviews = WorkgroupPeerReview.objects.filter(workgroup=pk)
        response_data = []
        if peer_reviews:
            for peer_review in peer_reviews:
                serializer = WorkgroupPeerReviewSerializer(peer_review)
                response_data.append(serializer.data)
        return Response(response_data, status=status.HTTP_200_OK)

    @link()
    def workgroup_reviews(self, request, pk):
        """
        View Workgroup Reviews for a specific Workgroup
        """
        workgroup_reviews = WorkgroupReview.objects.filter(workgroup=pk)
        response_data = []
        if workgroup_reviews:
            for workgroup_review in workgroup_reviews:
                serializer = WorkgroupReviewSerializer(workgroup_review)
                response_data.append(serializer.data)
        return Response(response_data, status=status.HTTP_200_OK)

    @link()
    def submissions(self, request, pk):
        """
        View Submissions for a specific Workgroup
        """
        submissions = WorkgroupSubmission.objects.filter(workgroup=pk)
        response_data = []
        if submissions:
            for submission in submissions:
                serializer = WorkgroupSubmissionSerializer(submission)
                response_data.append(serializer.data)
        return Response(response_data, status=status.HTTP_200_OK)

    @action()
    def grades(self, request, pk):
        """
        Submit a grade for a Workgroup.  The grade will be applied to all members of the workgroup
        """
        # Ensure we received all of the necessary information
        course_id = request.DATA.get('course_id')
        if course_id is None:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        try:
            course_descriptor = get_course(course_id)
        except ValueError:
            course_descriptor = None
        if not course_descriptor:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        content_id = request.DATA.get('content_id')
        if content_id is None:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        grade = request.DATA.get('grade')
        if grade is None:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        max_grade = request.DATA.get('max_grade')
        if max_grade is None:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        if grade > max_grade:
            max_grade = grade

        users = User.objects.filter(workgroups=pk)
        for user in users:
            key = KeyValueStore.Key(
                scope=Scope.user_state,
                user_id=user.id,
                block_scope_id=Location(content_id),
                field_name='grade'
            )
            field_data_cache = FieldDataCache([course_descriptor], course_id, user)
            student_module = field_data_cache.find_or_create(key)
            student_module.grade = grade
            student_module.max_grade = max_grade
            student_module.save()
        return Response({}, status=status.HTTP_201_CREATED)


class ProjectsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the Project model.
    """
    serializer_class = ProjectSerializer
    model = Project

    @action(methods=['get', 'post'])
    def workgroups(self, request, pk):
        """
        Add a Workgroup to a Project
        """
        if request.method == 'GET':
            workgroups = Workgroup.objects.filter(project=pk)
            response_data = []
            if workgroups:
                for workgroup in workgroups:
                    serializer = WorkgroupSerializer(workgroup)
                    response_data.append(serializer.data)
            return Response(response_data, status=status.HTTP_200_OK)
        else:
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


class WorkgroupSubmissionsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the Submission model.
    """
    serializer_class = WorkgroupSubmissionSerializer
    model = WorkgroupSubmission


class WorkgroupReviewsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the ProjectReview model.
    """
    serializer_class = WorkgroupReviewSerializer
    model = WorkgroupReview


class WorkgroupSubmissionReviewsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the SubmissionReview model.
    """
    serializer_class = WorkgroupSubmissionReviewSerializer
    model = WorkgroupSubmissionReview


class WorkgroupPeerReviewsViewSet(viewsets.ModelViewSet):
    """
    Django Rest Framework ViewSet for the PeerReview model.
    """
    serializer_class = WorkgroupPeerReviewSerializer
    model = WorkgroupPeerReview
