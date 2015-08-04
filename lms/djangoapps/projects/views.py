# pylint: disable=C0103
# pylint: disable=W0613

""" WORKGROUPS API VIEWS """
from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from rest_framework import viewsets
from rest_framework.decorators import action, link
from rest_framework import status
from rest_framework.response import Response

from xblock.fields import Scope
from courseware.models import StudentModule
from openedx.core.djangoapps.course_groups.models import CourseCohort
from xblock.runtime import KeyValueStore


from courseware import module_render
from courseware.courses import get_course
from courseware.model_data import FieldDataCache
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey, Location
from xmodule.modulestore import Location, InvalidLocationError
from xmodule.modulestore.django import modulestore
from openedx.core.djangoapps.course_groups.cohorts import (
    add_cohort, add_user_to_cohort, get_cohort_by_name, remove_user_from_cohort,
)

from .models import Project, Workgroup, WorkgroupSubmission
from .models import WorkgroupReview, WorkgroupSubmissionReview, WorkgroupPeerReview
from .serializers import UserSerializer, GroupSerializer
from .serializers import ProjectSerializer, WorkgroupSerializer, WorkgroupSubmissionSerializer
from .serializers import WorkgroupReviewSerializer, WorkgroupSubmissionReviewSerializer, WorkgroupPeerReviewSerializer


def _get_course(request, user, course_id, depth=0, load_content=False):
    """
    Utility method to obtain course components
    """
    course_descriptor = None
    course_key = None
    course_content = None
    try:
        course_key = CourseKey.from_string(course_id)
    except InvalidKeyError:
        try:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        except InvalidKeyError:
            pass
    if course_key:
        try:
            course_descriptor = get_course(course_key, depth=depth)
        except ValueError:
            pass
    if course_descriptor and load_content:
        field_data_cache = FieldDataCache([course_descriptor], course_key, user)
        course_content = module_render.get_module(
            user,
            request,
            course_descriptor.location,
            field_data_cache,
            course_key)
    return course_descriptor, course_key, course_content


def _get_course_child(request, user, course_key, content_id, load_content=False):
    """
    Return a course xmodule/xblock to the caller
    """
    content_descriptor = None
    content_key = None
    content = None
    try:
        content_key = UsageKey.from_string(content_id)
    except InvalidKeyError:
        try:
            content_key = Location.from_deprecated_string(content_id)
        except (InvalidKeyError, InvalidLocationError):
            pass
    if content_key:
        store = modulestore()
        content_descriptor = store.get_item(content_key)
    if content_descriptor and load_content:
        field_data_cache = FieldDataCache([content_descriptor], course_key, user)
        content = module_render.get_module(
            user,
            request,
            content_key,
            field_data_cache,
            course_key)
    return content_descriptor, content_key, content


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

    def create(self, request):
        """
        Create a new workgroup and its cohort.
        """
        assignment_type = request.DATA.get('assignment_type', CourseCohort.RANDOM)
        if assignment_type not in dict(CourseCohort.ASSIGNMENT_TYPE_CHOICES).keys():
            message = "Not a valid assignment type, '{}'".format(assignment_type)
            return Response({'details': message}, status.HTTP_400_BAD_REQUEST)
        response = super(WorkgroupsViewSet, self).create(request)
        if response.status_code == status.HTTP_201_CREATED:
            # create the workgroup cohort
            workgroup = self.object
            course_descriptor, course_key, course_content = _get_course(self.request, self.request.user, workgroup.project.course_id)  # pylint: disable=W0612
            add_cohort(course_key, workgroup.cohort_name, assignment_type)

        return response

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
                    response_data.append(serializer.data)  # pylint: disable=E1101
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
                    response_data.append(serializer.data)  # pylint: disable=E1101
            return Response(response_data, status=status.HTTP_200_OK)
        elif request.method == 'POST':
            user_id = request.DATA.get('id')
            try:
                user = User.objects.get(id=user_id)
            except ObjectDoesNotExist:
                message = 'User {} does not exist'.format(user_id)
                return Response({"detail": message}, status.HTTP_400_BAD_REQUEST)

            workgroup = self.get_object()

            # Ensure the user is not already assigned to a project for this course
            existing_projects = Project.objects.filter(course_id=workgroup.project.course_id).filter(workgroups__users__id=user.id)
            if len(existing_projects):
                message = 'User {} already assigned to a project for this course'.format(user_id)
                return Response({"detail": message}, status.HTTP_400_BAD_REQUEST)

            try:
                workgroup.add_user(user)
            except ValidationError as e:
                return Response({"detail": unicode(e)}, status.HTTP_400_BAD_REQUEST)

            workgroup.save()

            # add user to the workgroup cohort, create it if it doesn't exist (for cases where there is a legacy
            # workgroup)
            course_descriptor, course_key, course_content = _get_course(self.request, user, workgroup.project.course_id)  # pylint: disable=W0612
            try:
                cohort = get_cohort_by_name(course_key, workgroup.cohort_name)
                add_user_to_cohort(cohort, user.username)
            except ObjectDoesNotExist:
                # This use case handles cases where a workgroup might have been created before
                # the notion of a cohorted discussion. So we need to backfill in the data
                assignment_type = request.DATA.get('assignment_type', CourseCohort.RANDOM)
                if assignment_type not in dict(CourseCohort.ASSIGNMENT_TYPE_CHOICES).keys():
                    message = "Not a valid assignment type, '{}'".format(assignment_type)
                    return Response({"detail": message}, status.HTTP_400_BAD_REQUEST)
                cohort = add_cohort(course_key, workgroup.cohort_name, assignment_type)
                for workgroup_user in workgroup.users.all():
                    add_user_to_cohort(cohort, workgroup_user.username)
            return Response({}, status=status.HTTP_201_CREATED)
        else:
            user_id = request.DATA.get('id')
            try:
                user = User.objects.get(id=user_id)
            except ObjectDoesNotExist:
                message = 'User {} does not exist'.format(user_id)
                return Response({"detail": message}, status.HTTP_400_BAD_REQUEST)
            workgroup = self.get_object()
            course_descriptor, course_key, course_content = _get_course(self.request, user, workgroup.project.course_id)  # pylint: disable=W0612
            cohort = get_cohort_by_name(course_key,
                                        workgroup.cohort_name)
            workgroup.remove_user(user)
            remove_user_from_cohort(cohort, user.username)
            return Response({}, status=status.HTTP_204_NO_CONTENT)

    @link()
    def peer_reviews(self, request, pk):
        """
        View Peer Reviews for a specific Workgroup
        """
        peer_reviews = WorkgroupPeerReview.objects.filter(workgroup=pk)
        content_id = self.request.QUERY_PARAMS.get('content_id', None)
        if content_id is not None:
            peer_reviews = peer_reviews.filter(content_id=content_id)
        response_data = []
        if peer_reviews:
            for peer_review in peer_reviews:
                serializer = WorkgroupPeerReviewSerializer(peer_review)
                response_data.append(serializer.data)  # pylint: disable=E1101
        return Response(response_data, status=status.HTTP_200_OK)

    @link()
    def workgroup_reviews(self, request, pk):
        """
        View Workgroup Reviews for a specific Workgroup
        """
        workgroup_reviews = WorkgroupReview.objects.filter(workgroup=pk)
        content_id = self.request.QUERY_PARAMS.get('content_id', None)
        if content_id is not None:
            workgroup_reviews = workgroup_reviews.filter(content_id=content_id)

        response_data = []
        if workgroup_reviews:
            for workgroup_review in workgroup_reviews:
                serializer = WorkgroupReviewSerializer(workgroup_review)
                response_data.append(serializer.data)  # pylint: disable=E1101
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
                response_data.append(serializer.data)  # pylint: disable=E1101
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
        course_descriptor, course_key, course_content = _get_course(request, request.user, course_id)  # pylint: disable=W0612
        if not course_descriptor:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        content_id = request.DATA.get('content_id')
        if content_id is None:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)
        content_descriptor, content_key, content = _get_course_child(request, request.user, course_key, content_id)  # pylint: disable=W0612
        if content_descriptor is None:
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
            module, created = StudentModule.objects.get_or_create(
                student_id=user.id,
                module_state_key=content_key,
                course_id=course_key,
            )
            module.grade = grade
            module.max_grade = max_grade
            module.save()
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
                    response_data.append(serializer.data)  # pylint: disable=E1101
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
