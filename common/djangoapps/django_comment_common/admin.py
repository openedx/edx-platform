'''
django admin pages for courseware model
'''

from django_comment_common.models import Role,Permission
from ratelimitbackend import admin

admin.site.register(Role)

admin.site.register(Permission)
