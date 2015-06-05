"""
Django admin page for credit eligibility
"""
from ratelimitbackend import admin
from .models import CreditCourse, CreditProvider

admin.site.register(CreditCourse)
admin.site.register(CreditProvider)
