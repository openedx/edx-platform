from django.contrib import admin

from .models import DigitalBookAccess

@admin.register(DigitalBookAccess)
class DigitalBookAccessAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'uuid',
        'digital_book_key'
    )
    raw_id_fields = ('user',)
