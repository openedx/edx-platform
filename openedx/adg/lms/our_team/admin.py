"""
Registering models for our team app.
"""
from django.contrib import admin

from .models import OurTeamMember


@admin.register(OurTeamMember)
class OurTeamMemberAdmin(admin.ModelAdmin):
    """
    Django admin class for OurTeamMember
    """

    list_display = ('id', 'name', 'designation', 'image', 'description',)
    list_filter = ('designation',)
    search_fields = ('name',)
