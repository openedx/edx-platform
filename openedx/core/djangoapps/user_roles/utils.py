# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from .models import UserRoleResource


def get_role_auth_claim_for_user(user):
    role_resources = UserRoleResource.objects.filter(user_email=user.email)
    authorization_claim = []
    for role_resource in role_resources:
        authorization_claim.append('{role}:{object_type}:{object_key}'.format(
            role=role_resource.role,
            object_type=role_resource.object_type,
            object_key=role_resource.object_key,
        ))

    return authorization_claim
