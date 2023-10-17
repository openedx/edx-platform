from django.core.validators import ValidationError

from openedx.features.genplus_features.genplus.models import GenUser, School, Student
from openedx.features.genplus_features.genplus.constants import GenUserRoles
from openedx.features.genplus_features.genplus_learning.utils import (
    process_pending_student_program_enrollments,
    process_pending_teacher_program_access
)
from .constants import SchoolTypes

def validate_role(role):
    if not role in GenUserRoles.__ALL__:
        raise ValidationError("Role not found in choices")

def get_or_create_school(organisation_id, organisation_name):
    school, created = School.objects.get_or_create(
        guid=organisation_id,
        type=SchoolTypes.RM_UNIFY,
        name=organisation_name
    )
    if created:
        school.is_active = False
        school.save()
    return school

def create_gen_user(user, role, identity_guid, year_of_entry, registration_group, school):
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
    return gen_user

def process_gen_user_enrollments(gen_user):
    if gen_user.is_student:
        process_pending_student_program_enrollments(gen_user)
    elif gen_user.is_teacher:
        process_pending_teacher_program_access(gen_user)

def register_rm_unify_gen_user(user, gen_user_data):
    role = gen_user_data.get('role', '')
    validate_role(role)

    organisation_id = gen_user_data.get('organisation_id')
    organisation_name = gen_user_data.get('organisation_name')

    school = None
    if organisation_id and organisation_name:
        school = get_or_create_school(organisation_id, organisation_name)

    if not school:
        raise ValidationError("School not found for this gen user")

    year_of_entry = gen_user_data.get('year_of_entry')
    registration_group = gen_user_data.get('registration_group')
    identity_guid = gen_user_data.get('identity_guid', '')

    gen_user = create_gen_user(user, role, identity_guid, year_of_entry, registration_group, school)
    process_gen_user_enrollments(gen_user)

def register_xporter_gen_user(user, gen_user_data):
    role = gen_user_data.get('role', None)
    scn = gen_user_data.get('scn', None)
    gen_user = None

    if role and role.lower() in GenUserRoles.TEACHING_ROLES:
        role = GenUserRoles.XPORTER_TEACHING_STAFF
    else:
        role = GenUserRoles.STUDENT
    if role == GenUserRoles.STUDENT and scn is None:
        raise ValidationError('SCN is missing in the claims')
    organisation_cost_center = gen_user_data.get('organisation')
    try:
        school = School.objects.get(cost_center=organisation_cost_center)
    except School.DoesNotExist:
        raise ValidationError('School not found')

    if role not in GenUserRoles.TEACHING_ROLES:
        try:
            student = Student.objects.get(scn=scn)
            # update the email with the sso claimed email. (in case of xporter it can be differentiated)
            gen_user = student.gen_user
            gen_user.email = user.email
            gen_user.user = user
            gen_user.school = school
            gen_user.save()
        except Student.DoesNotExist:
            gen_user = create_gen_user(user, role, '', '', '', school)
            gen_user.refresh_from_db()
            gen_user.student.scn = scn
            gen_user.student.save()
        except Student.MultipleObjectsReturned:
            raise ValidationError('Multiple student exists with this SCN')
    elif role in GenUserRoles.TEACHING_ROLES:
        try:
            gen_user = GenUser.objects.get(email=user.email)
            gen_user.user = user
            gen_user.school = school
            gen_user.save()
        except GenUser.DoesNotExist:
            gen_user = create_gen_user(user, role, '', '', '', school)
    process_gen_user_enrollments(gen_user)
