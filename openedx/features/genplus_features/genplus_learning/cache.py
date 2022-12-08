from django.core.cache import cache
from django.db.models import Q
from django.apps import apps
from collections import defaultdict
from openedx.core.lib.cache_utils import get_cache
from openedx.features.genplus_features.genplus_learning.models import Program, ProgramAccessRole


class BulkRoleCache:  # lint-amnesty, pylint: disable=missing-class-docstring
    CACHE_NAMESPACE = "genplus.roles.BulkRoleCache"
    CACHE_KEY = 'program_roles_by_user'

    @classmethod
    def prefetch(cls, users):  # lint-amnesty, pylint: disable=missing-function-docstring
        roles_by_user = defaultdict(set)
        get_cache(cls.CACHE_NAMESPACE)[cls.CACHE_KEY] = roles_by_user

        for role in ProgramAccessRole.objects.filter(user__in=users).select_related('user'):
            roles_by_user[role.user.id].add(role)

        users_without_roles = [u for u in users if u.id not in roles_by_user]
        for user in users_without_roles:
            roles_by_user[user.id] = set()

    @classmethod
    def get_user_roles(cls, user):
        return get_cache(cls.CACHE_NAMESPACE)[cls.CACHE_KEY][user.id]


class ProgramRoleCache:
    """
    A cache of the ProgramAccessRoles held by a particular user
    """
    def __init__(self, user):
        try:
            self._program_roles = BulkRoleCache.get_user_roles(user)
        except KeyError:
            self._program_roles = set(
                ProgramAccessRole.objects.filter(user=user).all()
            )

    def has_role(self, role, program):
        """
        Return whether this ProgramRoleCache contains a role with the specified role, program_id
        """
        return any(
            access_role.role == role and
            access_role.program == program
            for access_role in self._program_roles
        )

class ProgramCache:
    CACHE_KEY = 'course_program_mapping'

    @classmethod
    def find_course_mapping(cls, course_key):
        """
        This function checks if course is part of any program and returns the program instance
        It caches the program instance as well
        """
        course_key_str = str(course_key)
        cache_key = f'{cls.CACHE_KEY}-{str(course_key)}'
        program = cache.get(cache_key)
        if program:
            return program

        programs = Program.objects.filter(Q(intro_unit=course_key) | Q(outro_unit=course_key) | Q(units__course=course_key)).distinct()
        # A course should exist only in one program
        if programs.count() == 1:
            program = programs.first()
            cache.set(key=cache_key, value=program, timeout=None)

        return program

    @classmethod
    def clear_course_mapping(cls, course_key):
        course_key_str = str(course_key)
        cache_key = f'{cls.CACHE_KEY}-{str(course_key)}'
        cache.delete(cache_key)

    @classmethod
    def clear_mapping_for_all_courses(cls, program: Program):
        for course_key in program.all_units_ids:
            cls.clear_course_mapping(course_key)
