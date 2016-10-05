from django.contrib import admin

from .models import EnterpriseCustomer


@admin.register(EnterpriseCustomer)
class EnterpriseCustomerAdmin(admin.ModelAdmin):
    pass