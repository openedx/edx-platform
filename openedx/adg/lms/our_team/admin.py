"""
Registering models for our team app.
"""
from django.contrib import admin

from .models import OurTeamMember


@admin.register(OurTeamMember)
class ApplicationHubAdmin(admin.ModelAdmin):
    """
    Django admin class for OurTeam
    """

    fields = ('name', 'designation', 'image', 'description', 'url',)
    list_display = ('id', 'name', 'designation', 'image', 'description',)
    list_filter = ('name',)
    search_fields = ('name',)
