"""
Admin for managing the connection to the Forums backend service.
"""


from django.contrib import admin

from .models import ForumsConfig

admin.site.register(ForumsConfig)
