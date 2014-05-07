""" API implementation for group-oriented interactions. """
import uuid
import json
from collections import OrderedDict

from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from api_manager.permissions import ApiKeyHeaderPermission
from api_manager.models import GroupRelationship, CourseGroupRelationship, GroupProfile
from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location, InvalidLocationError

RELATIONSHIP_TYPES = {'hierarchical': 'h', 'graph': 'g'}


def _generate_base_uri(request):
    """
    Constructs the protocol:host:path component of the resource uri
    """
    protocol = 'http'
    if request.is_secure():
        protocol = protocol + 's'
    resource_uri = '{}://{}{}'.format(
        protocol,
        request.get_host(),
        request.get_full_path()
    )
    return resource_uri


class GroupsList(APIView):
    permissions_classes = (ApiKeyHeaderPermission,)

    def post(self, request):
        """
        POST creates a new group in the system
        """
        response_data = {}
        base_uri = _generate_base_uri(request)
        # Group name must be unique, but we need to support dupes
        group = Group.objects.create(name=str(uuid.uuid4()))
        if request.DATA.get('name'):
            original_group_name = request.DATA.get('name')
        else:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        group.name = '{:04d}: {}'.format(group.id, original_group_name)
        group.record_active = True
        group.record_date_created = timezone.now()
        group.record_date_modified = timezone.now()
        group.save()

        # Create a corresponding relationship management record
        GroupRelationship.objects.create(group_id=group.id, parent_group=None)

        # Create a corresponding profile record (for extra meta info)
        group_type = request.DATA.get('group_type', None)
        data = json.dumps(request.DATA.get('data')) if request.DATA.get('data') else {}
        profile, _ = GroupProfile.objects.get_or_create(group_id=group.id, group_type=group_type, name=original_group_name, data=data)

        response_data = {
            'id': group.id,
            'name': original_group_name,
            'type': group_type,
        }
        base_uri = _generate_base_uri(request)
        response_data['uri'] = '{}/{}'.format(base_uri, group.id)
        response_status = status.HTTP_201_CREATED
        return Response(response_data, status=response_status)

    def get(self, request):
        """
        GET retrieves a list of groups in the system filtered by type
        """
        response_data = []
        if 'type' in request.GET:
            profiles = GroupProfile.objects.filter(group_type=request.GET['type'])
        else:
            profiles = GroupProfile.objects.all()
        for profile in profiles:
            item_data = {}
            item_data['group_id'] = profile.group_id
            if profile.name and len(profile.name):
                group_name = profile.name
            else:
                group = Group.objects.get(id=profile.group_id)
                group_name = group.name
            item_data['name'] = group_name
            if profile.group_type:
                item_data['group_type'] = profile.group_type
            if profile.data:
                item_data['data'] = json.loads(profile.data)
            response_data.append(item_data)
        return Response(response_data, status=status.HTTP_200_OK)


class GroupsDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request, group_id):
        response_data = {}
        base_uri = _generate_base_uri(request)
        print base_uri
        try:
            existing_group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            return Response({}, status.HTTP_404_NOT_FOUND)
        group_type = request.DATA.get('group_type')
        data = json.dumps(request.DATA.get('data')) if request.DATA.get('data') else None
        if not group_type and not data:
            return Response({}, status.HTTP_400_BAD_REQUEST)
        profile, _ = GroupProfile.objects.get_or_create(group_id=group_id)
        profile.group_type = group_type
        profile.data = data
        profile.save()
        response_data['id'] = existing_group.id
        response_data['name'] = profile.name
        response_data['uri'] = _generate_base_uri(request)
        return Response(response_data, status=status.HTTP_201_CREATED)

    def get(self, request, group_id):
        """
        GET retrieves an existing group from the system
        """
        response_data = {}
        base_uri = _generate_base_uri(request)
        try:
            existing_group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            return Response({}, status.HTTP_404_NOT_FOUND)
        response_data['id'] = existing_group.id
        response_data['uri'] = base_uri
        response_data['resources'] = []
        resource_uri = '{}/users'.format(base_uri)
        response_data['resources'].append({'uri': resource_uri})
        resource_uri = '{}/groups'.format(base_uri)
        response_data['resources'].append({'uri': resource_uri})
        try:
            group_profile = GroupProfile.objects.get(group_id=group_id)
        except ObjectDoesNotExist:
            group_profile = None
        if group_profile:
            if group_profile.name:
                response_data['name'] = group_profile.name
            else:
                response_data['name'] = existing_group.name
            if group_profile.group_type:
                response_data['group_type'] = group_profile.group_type
            data = group_profile.data
            if data:
                response_data['data'] = json.loads(data)
        else:
            response_data['name'] = existing_group.name
        return Response(response_data, status=status.HTTP_200_OK)


class GroupsUsersList(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request, group_id):
        """
        POST creates a new group-user relationship in the system
        """
        base_uri = _generate_base_uri(request)
        try:
            existing_group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            return Response({}, status.HTTP_404_NOT_FOUND)
        user_id = request.DATA['user_id']
        try:
            existing_user = User.objects.get(id=user_id)
        except ObjectDoesNotExist:
            return Response({}, status.HTTP_404_NOT_FOUND)
        try:
            existing_relationship = Group.objects.get(user=existing_user)
        except ObjectDoesNotExist:
            existing_relationship = None
        response_data = {}
        if existing_relationship is None:
            existing_group.user_set.add(existing_user.id)
            response_data['uri'] = '{}/{}'.format(base_uri, existing_user.id)
            response_data['group_id'] = str(existing_group.id)
            response_data['user_id'] = str(existing_user.id)
            response_status = status.HTTP_201_CREATED
        else:
            response_data['uri'] = '{}/{}'.format(base_uri, existing_user.id)
            response_data['message'] = "Relationship already exists."
            response_status = status.HTTP_409_CONFLICT
        return Response(response_data, status=response_status)

    def get(self, request, group_id):
        """
        GET retrieves the list of users related to the specified group
        """
        try:
            existing_group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            return Response({}, status.HTTP_404_NOT_FOUND)
        users = existing_group.user_set.all()
        response_data = {}
        response_data['users'] = []
        for user in users:
            user_data = {}
            user_data['id'] = user.id
            user_data['email'] = user.email
            user_data['username'] = user.username
            user_data['first_name'] = user.first_name
            user_data['last_name'] = user.last_name
            response_data['users'].append(user_data)
        response_status = status.HTTP_200_OK
        return Response(response_data, status=response_status)


class GroupsUsersDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, group_id, user_id):
        """
        GET retrieves an existing group-user relationship from the system
        """
        response_data = {}
        base_uri = _generate_base_uri(request)
        try:
            existing_group = Group.objects.get(id=group_id)
            existing_relationship = existing_group.user_set.get(id=user_id)
        except ObjectDoesNotExist:
            existing_group = None
            existing_relationship = None
        if existing_group and existing_relationship:
            response_data['group_id'] = existing_group.id
            response_data['user_id'] = existing_relationship.id
            response_data['uri'] = base_uri
            response_status = status.HTTP_200_OK
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)

    def delete(self, request, group_id, user_id):
        """
        DELETE removes/inactivates/etc. an existing group-user relationship
        """
        try:
            existing_group = Group.objects.get(id=group_id)
            existing_group.user_set.remove(user_id)
            existing_group.save()
        except ObjectDoesNotExist:
            pass
        return Response({}, status=status.HTTP_204_NO_CONTENT)


class GroupsGroupsList(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request, group_id):
        """
        POST creates a new group-group relationship in the system
        """
        response_data = {}
        to_group_id = request.DATA['group_id']
        relationship_type = request.DATA['relationship_type']
        base_uri = _generate_base_uri(request)
        response_data['uri'] = '{}/{}'.format(base_uri, to_group_id)
        response_data['group_id'] = str(to_group_id)
        response_data['relationship_type'] = relationship_type
        try:
            from_group_relationship = GroupRelationship.objects.get(group__id=group_id)
            to_group_relationship = GroupRelationship.objects.get(group__id=to_group_id)
        except ObjectDoesNotExist:
            from_group_relationship = None
            to_group_relationship = None
        if from_group_relationship and to_group_relationship:
            response_status = status.HTTP_201_CREATED
            if relationship_type == RELATIONSHIP_TYPES['hierarchical']:
                to_group_relationship.parent_group = from_group_relationship
                to_group_relationship.save()
            elif relationship_type == RELATIONSHIP_TYPES['graph']:
                from_group_relationship.add_linked_group_relationship(to_group_relationship)
            else:
                response_data['message'] = "Relationship type '%s' not currently supported" % relationship_type
                response_data['field_conflict'] = 'relationship_type'
                response_status = status.HTTP_406_NOT_ACCEPTABLE
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)

    def get(self, request, group_id):
        """
        GET retrieves the existing group-group relationships for the specified group
        """
        try:
            from_group_relationship = GroupRelationship.objects.get(group__id=group_id)
        except ObjectDoesNotExist:
            from_group_relationship = None
        response_data = []
        if from_group_relationship:
            base_uri = _generate_base_uri(request)
            group_type = request.QUERY_PARAMS.get('type', None)
            child_groups = GroupRelationship.objects.filter(parent_group_id=group_id)
            linked_groups = from_group_relationship.get_linked_group_relationships()
            if group_type:
                profiles = GroupProfile.objects.filter(group_type=request.GET['type']).values_list('group_id', flat=True)
                if profiles:
                    child_groups = child_groups.filter(group_id__in=profiles)
                    linked_groups = linked_groups.filter(to_group_relationship__in=profiles)
            if child_groups:
                for group in child_groups:
                    response_data.append({
                        "id": group.group_id,
                        "relationship_type": RELATIONSHIP_TYPES['hierarchical'],
                        "uri": '{}/{}'.format(base_uri, group.group.id)
                    })
            if linked_groups:
                for group in linked_groups:
                    response_data.append({
                        "id": group.to_group_relationship_id,
                        "relationship_type": RELATIONSHIP_TYPES['graph'],
                        "uri": '{}/{}'.format(base_uri, group.to_group_relationship_id)
                    })
            response_status = status.HTTP_200_OK
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)


class GroupsGroupsDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, group_id, related_group_id):
        """
        GET retrieves an existing group-group relationship from the system
        """
        response_data = {}
        base_uri = _generate_base_uri(request)
        response_data['uri'] = base_uri
        response_data['from_group_id'] = group_id
        response_data['to_group_id'] = related_group_id
        response_status = status.HTTP_404_NOT_FOUND
        from_group_relationship = GroupRelationship.objects.get(group__id=group_id)
        if from_group_relationship:
            to_group_relationship = GroupRelationship.objects.get(group__id=related_group_id)
            if to_group_relationship and str(to_group_relationship.parent_group_id) == str(group_id):
                response_data['relationship_type'] = RELATIONSHIP_TYPES['hierarchical']
                response_status = status.HTTP_200_OK
            else:
                to_group = Group.objects.get(id=to_group_relationship.group_id)
                linked_group_exists = from_group_relationship.check_linked_group_relationship(to_group, symmetrical=True)
                if linked_group_exists:
                    response_data['relationship_type'] = RELATIONSHIP_TYPES['graph']
                    response_status = status.HTTP_200_OK
        return Response(response_data, response_status)

    def delete(self, request, group_id, related_group_id):
        """
        DELETE removes/inactivates/etc. an existing group-group relationship
        """
        try:
            from_group_relationship = GroupRelationship.objects.get(group__id=group_id)
        except ObjectDoesNotExist:
            from_group_relationship = None
        try:
            to_group_relationship = GroupRelationship.objects.get(group__id=related_group_id)
        except ObjectDoesNotExist:
            to_group = None
            to_group_relationship = None
        if from_group_relationship:
            if to_group_relationship:
                if to_group_relationship.parent_group_id is from_group_relationship.group_id:
                    to_group_relationship.parent_group_id = None
                    to_group_relationship.save()
                else:
                    from_group_relationship.remove_linked_group_relationship(to_group_relationship)
                    from_group_relationship.save()
            # No 'else' clause here -> It's ok if we didn't find a match
            response_status = status.HTTP_204_NO_CONTENT
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response({}, status=response_status)


class GroupsCoursesList(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def post(self, request, group_id):
        """
        POST creates a new group-course relationship in the system
        """
        response_data = {}
        try:
            existing_group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            return Response({}, status.HTTP_404_NOT_FOUND)
        store = modulestore()
        course_id = request.DATA['course_id']

        base_uri = _generate_base_uri(request)
        response_data['uri'] = '{}/{}'.format(base_uri, course_id)

        existing_course = store.get_course(course_id)
        if not existing_course:
            return Response({}, status.HTTP_404_NOT_FOUND)

        try:
            existing_relationship = CourseGroupRelationship.objects.get(course_id=course_id, group=existing_group)
        except ObjectDoesNotExist:
            existing_relationship = None

        if existing_relationship is None:
            new_relationship = CourseGroupRelationship.objects.create(course_id=course_id, group=existing_group)
            response_data['group_id'] = str(new_relationship.group_id)
            response_data['course_id'] = str(new_relationship.course_id)
            response_status = status.HTTP_201_CREATED
        else:
            response_data['message'] = "Relationship already exists."
            response_status = status.HTTP_409_CONFLICT
        return Response(response_data, status=response_status)

    def get(self, request, group_id):
        """
        GET returns all courses that has a relationship to the group
        """
        response_data = {}
        try:
            existing_group = Group.objects.get(id=group_id)
        except ObjectDoesNotExist:
            return Response({}, status.HTTP_404_NOT_FOUND)
        store = modulestore()
        members = CourseGroupRelationship.objects.filter(group=existing_group)
        response_data['courses'] = []
        for member in members:
            course = store.get_course(member.course_id)
            course_data = {
                'course_id': member.course_id,
                'display_name': course.display_name
            }
            response_data['courses'].append(course_data)
        response_status = status.HTTP_200_OK
        return Response(response_data, status=response_status)


class GroupsCoursesDetail(APIView):
    permission_classes = (ApiKeyHeaderPermission,)

    def get(self, request, group_id, course_id):
        """
        GET retrieves an existing group-course relationship from the system
        """
        response_data = {}
        base_uri = _generate_base_uri(request)
        response_data['uri'] = base_uri
        try:
            existing_group = Group.objects.get(id=group_id)
            existing_relationship = CourseGroupRelationship.objects.get(course_id=course_id, group=existing_group)
        except ObjectDoesNotExist:
            existing_group = None
            existing_relationship = None
        if existing_group and existing_relationship:
            response_data['group_id'] = existing_group.id
            response_data['course_id'] = existing_relationship.course_id
            response_status = status.HTTP_200_OK
        else:
            response_status = status.HTTP_404_NOT_FOUND
        return Response(response_data, status=response_status)

    def delete(self, request, group_id, course_id):
        """
        DELETE removes/inactivates/etc. an existing group-course relationship
        """
        try:
            existing_group = Group.objects.get(id=group_id)
            existing_group.coursegrouprelationship_set.get(course_id=course_id).delete()
            existing_group.save()
        except ObjectDoesNotExist:
            pass
        return Response({}, status=status.HTTP_204_NO_CONTENT)
