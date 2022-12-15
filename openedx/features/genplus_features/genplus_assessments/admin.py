from django.contrib import admin
from openedx.features.genplus_features.genplus_assessments.models import UserResponse, UserRating


@admin.register(UserResponse)
class UserResponseAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UserResponse._meta.get_fields()]


@admin.register(UserRating)
class UserResponseAdmin(admin.ModelAdmin):
    list_display = [field.name for field in UserRating._meta.get_fields()]
