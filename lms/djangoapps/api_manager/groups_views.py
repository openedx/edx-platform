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
        request.path
    )
    return resource_uri


@api_view(['GET', 'POST'])
@permission_classes((ApiKeyHeaderPermission,))
def group_list(request):
    """
    GET retrieves a list of groups in the system filtered by type
    POST creates a new group in the system
    """
    if request.method == 'GET':
        if not 'type' in request.GET:
            return Response({}, status=status.HTTP_400_BAD_REQUEST)

        response_data = []
        profiles = GroupProfile.objects.filter(group_type=request.GET['type'])
        for profile in profiles:
            item_data = {}
            item_data['group_id'] = profile.group_id
            if profile.group_type:
                item_data['group_type'] = profile.group_type

            if profile.data:
                item_data['data'] = json.loads(profile.data)
            response_data.append(item_data)

        return Response(response_data)
    elif request.method == 'POST':
        response_data = {}
        base_uri = _generate_base_uri(request)
        # Group name must be unique, but we need to support dupes
        group = Group.objects.create(name=str(uuid.uuid4()))
        original_group_name = request.DATA['name']

        group.name = '{:04d}: {}'.format(group.id, original_group_name)
        group.record_active = True
        group.record_date_created = timezone.now()
        group.record_date_modified = timezone.now()
        group.save()

        # Relationship model also allows us to use duplicate names
        GroupRelationship.objects.create(name=original_group_name, group_id=group.id, parent_group=None)

        # allow for optional meta information about groups, this will end up in the GroupProfile table
        group_type = request.DATA.get('group_type')
        data = json.dumps(request.DATA.get('data'))

        if group_type or data:
            profile, _ = GroupProfile.objects.get_or_create(group_id=group.id, group_type=group_type, data=data)

        response_data = {'id': group.id, 'name': original_group_name}
        base_uri = _generate_base_uri(request)
        response_data['uri'] = '{}/{}'.format(base_uri, group.id)
        response_status = status.HTTP_201_CREATED
        return Response(response_data, status=response_status)


@api_view(['GET', 'POST'])
@permission_classes((ApiKeyHeaderPermission,))
def group_detail(request, group_id):
    """
    GET retrieves an existing group from the system
    """

    response_data = {}
    base_uri = _generate_base_uri(request)
    try:
        existing_group = Group.objects.get(id=group_id)
        existing_group_relationship = GroupRelationship.objects.get(group_id=group_id)
    except ObjectDoesNotExist:
        return Response({}, status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        response_data['name'] = existing_group_relationship.name
        response_data['id'] = existing_group.id
        response_data['uri'] = base_uri
        response_data['resources'] = []
        resource_uri = '{}/users'.format(base_uri)
        response_data['resources'].append({'uri': resource_uri})
        resource_uri = '{}/groups'.format(base_uri)
        response_data['resources'].append({'uri': resource_uri})

        # see if there is an (optional) GroupProfile
        try:
            existing_group_profile = GroupProfile.objects.get(group_id=group_id)
            if existing_group_profile.group_type:
                response_data['group_type'] = existing_group_profile.group_type
            data = existing_group_profile.data
            if data:
                response_data['data'] = json.loads(data)
        except ObjectDoesNotExist:
            pass

        response_status = status.HTTP_200_OK

        return Response(response_data, status=response_status)
    elif request.method == 'POST':
        # update GroupProfile data

        group_type = request.DATA.get('group_type')
        data = request.DATA.get('data')

        if not group_type and not data:
            return Response({}, status.HTTP_400_BAD_REQUEST)

        profile, _ = GroupProfile.objects.get_or_create(group_id=group_id)
        profile.group_type = group_type
        profile.data = data
        profile.save()

        return Response({})


@api_view(['POST'])
@permission_classes((ApiKeyHeaderPermission,))
def group_users_list(request, group_id):
    """
    POST creates a new group-user relationship in the system
    """
    response_data = {}
    group_id = group_id
    user_id = request.DATA['user_id']
    base_uri = _generate_base_uri(request)
    try:
        existing_group = Group.objects.get(id=group_id)
        existing_user = User.objects.get(id=user_id)
    except ObjectDoesNotExist:
        existing_group = None
        existing_user = None
    if existing_group and existing_user:
        try:
            existing_relationship = Group.objects.get(user=existing_user)
        except ObjectDoesNotExist:
            existing_relationship = None
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
    else:
        response_status = status.HTTP_404_NOT_FOUND
    return Response(response_data, status=response_status)


@api_view(['GET', 'DELETE'])
@permission_classes((ApiKeyHeaderPermission,))
def group_users_detail(request, group_id, user_id):
    """
    GET retrieves an existing group-user relationship from the system
    DELETE removes/inactivates/etc. an existing group-user relationship
    """
    if request.method == 'GET':
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
    elif request.method == 'DELETE':
        try:
            existing_group = Group.objects.get(id=group_id)
            existing_group.user_set.remove(user_id)
            existing_group.save()
        except ObjectDoesNotExist:
            pass
        return Response({}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST', 'GET'])
@permission_classes((ApiKeyHeaderPermission,))
def group_groups_list(request, group_id):
    """
    POST creates a new group-group relationship in the system
    GET retrieves the existing group-group relationships for the specified group
    """
    if request.method == 'POST':
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
    elif request.method == 'GET':
        try:
            from_group_relationship = GroupRelationship.objects.get(group__id=group_id)
        except ObjectDoesNotExist:
            from_group_relationship = None
        response_data = []
        if from_group_relationship:
            base_uri = _generate_base_uri(request)
            child_groups = GroupRelationship.objects.filter(parent_group_id=group_id)
            if child_groups:
                for group in child_groups:
                    response_data.append({
                                         "id": group.group_id,
                                         "relationship_type": RELATIONSHIP_TYPES['hierarchical'],
                                         "uri": '{}/{}'.format(base_uri, group.group.id)
                                         })
            linked_groups = from_group_relationship.get_linked_group_relationships()
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


@api_view(['GET', 'DELETE'])
@permission_classes((ApiKeyHeaderPermission,))
def group_groups_detail(request, group_id, related_group_id):
    """
    GET retrieves an existing group-group relationship from the system
    DELETE removes/inactivates/etc. an existing group-group relationship
    """
    if request.method == 'GET':
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
    elif request.method == 'DELETE':
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


@api_view(['GET', 'POST'])
@permission_classes((ApiKeyHeaderPermission,))
def group_courses_list(request, group_id):
    """
    GET returns all courses that has a relationship to the group
    POST creates a new group-course relationship in the system
    """
    response_data = {}

    try:
        existing_group = Group.objects.get(id=group_id)
    except ObjectDoesNotExist:
        return Response({}, status.HTTP_404_NOT_FOUND)

    store = modulestore()

    if request.method == 'GET':
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
    else:
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


@api_view(['GET', 'DELETE'])
@permission_classes((ApiKeyHeaderPermission,))
def group_courses_detail(request, group_id, course_id):
    """
    GET retrieves an existing group-course relationship from the system
    DELETE removes/inactivates/etc. an existing group-course relationship
    """
    if request.method == 'GET':
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
    elif request.method == 'DELETE':
        try:
            existing_group = Group.objects.get(id=group_id)
            existing_group.coursegrouprelationship_set.get(course_id=course_id).delete()
            existing_group.save()
        except ObjectDoesNotExist:
            pass
        return Response({}, status=status.HTTP_204_NO_CONTENT)
