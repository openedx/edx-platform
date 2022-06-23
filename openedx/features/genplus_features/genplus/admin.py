from django.contrib import admin
from openedx.features.genplus_features.genplus.models import GenUser, School, Character, Class, Student, Teacher
from openedx.features.genplus_features.genplus_learning.models import YearGroup, Skill

@admin.register(GenUser)
class GenUserAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'role',
        'school',
        'year_of_entry',
        'registration_group'
    )
    search_fields = ('user',)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = (
        'guid',
        'name',
        'external_id'
    )
    search_fields = ('name',)


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    filter_horizontal = ('skills',)
    search_fields = ('name',)


@admin.register(YearGroup)
class YearGroupAdmin(admin.ModelAdmin):
    search_fields = ('name', 'year_of_programme')


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'is_visible'
    )

    search_fields = ('name',)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    search_fields = ('name',)


# TODO: Remove after testing the login flow
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    filter_horizontal = ('classes',)

admin.site.register(Student)
