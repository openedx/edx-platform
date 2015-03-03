"""
django admin pages for branding model
"""

from ratelimitbackend import admin

from branding_stanford.models import TileConfiguration


class TileAdmin(admin.ModelAdmin):
    """
    List displayed when Tiles are listed.
    """

    list_display = (
        'course_id',
        'site',
        'enabled',
        'change_date',
        'changed_by',
    )

admin.site.register(TileConfiguration, TileAdmin)
