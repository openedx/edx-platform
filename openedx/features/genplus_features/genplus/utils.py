from django.core.validators import ValidationError

from openedx.features.genplus_features.genplus.models import GenUser, School
from openedx.features.genplus_features.genplus.constants import GenUserRoles
from openedx.features.genplus_features.genplus_learning.utils import (
    process_pending_student_program_enrollments,
    process_pending_teacher_program_access
)


def register_gen_user(user, gen_user_data):
    role = gen_user_data.get('role', '')
    # required field in genplus user registration
    if not role in GenUserRoles.__ALL__:
        raise ValidationError("Role not found in choices")

    organisation_id = gen_user_data.get('organisation_id')
    organisation_name = gen_user_data.get('organisation_name')

    school = None
    if organisation_id and organisation_name:
        school, created = School.objects.get_or_create(guid=organisation_id, name=organisation_name)

    # required field in genplus user registration
    if not school:
        raise ValidationError("School not found for this gen user")

    # optional fields in genplus user registration
    year_of_entry = gen_user_data.get('year_of_entry')
    registration_group = gen_user_data.get('registration_group')
    identity_guid = gen_user_data.get('identity_guid', '')

    try:
        gen_user = GenUser.objects.get(email=user.email)
        gen_user.user = user
        gen_user.school = school
        gen_user.save()

    except GenUser.DoesNotExist:
        gen_user = GenUser.objects.create(
            email=user.email,
            user=user,
            role=role,
            identity_guid=identity_guid,
            year_of_entry=year_of_entry,
            registration_group=registration_group,
            school=school
        )

    if gen_user.is_student:
        process_pending_student_program_enrollments(gen_user)
    elif gen_user.is_teacher:
        process_pending_teacher_program_access(gen_user)
