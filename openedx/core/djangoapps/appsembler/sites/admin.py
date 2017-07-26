from django.contrib.auth.models import User
from hijack_admin.admin import HijackUserAdminMixin
from ratelimitbackend import admin
from student.admin import UserAdmin
from .models import AlternativeDomain


class HijackableUserAdmin(UserAdmin, HijackUserAdminMixin):
    list_display = UserAdmin.list_display + (
        'hijack_field',
    )

admin.site.unregister(User)
admin.site.register(User, HijackableUserAdmin)
admin.site.register(AlternativeDomain)
