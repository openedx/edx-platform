from django.contrib import admin
from .models import TokenStorage


class TokenStorageAdmin(admin.ModelAdmin):
    fields = ['secret_token']

admin.site.register(TokenStorage, TokenStorageAdmin)
