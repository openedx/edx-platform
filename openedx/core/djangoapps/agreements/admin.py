"""
Django admin page for the Agreements app
"""

from django.contrib import admin

from openedx.core.djangoapps.agreements.models import IntegritySignature


class IntegritySignatureAdmin(admin.ModelAdmin):
    """
    Admin for the IntegritySignature Model
    """
    list_display = ('user', 'course_key', 'created', 'modified')
    readonly_fields = ('user', 'course_key', 'created', 'modified')
    search_fields = ('user__username', 'course_key',)
    ordering = ['-modified']

    class Meta:
        model = IntegritySignature


admin.site.register(IntegritySignature, IntegritySignatureAdmin)
