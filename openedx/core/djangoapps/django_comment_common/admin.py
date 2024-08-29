"""
Admin for managing the connection to the Forums backend service.
"""


from django.contrib import admin

from .models import ForumsConfig, Role,DiscussionsIdMapping, User

admin.site.register(ForumsConfig)
admin.site.register(Role)
admin.site.register(DiscussionsIdMapping)
# admin.site.register(User)

