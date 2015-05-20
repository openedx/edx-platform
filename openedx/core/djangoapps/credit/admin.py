"""
Django admin page for credit eligibility
"""
from ratelimitbackend import admin
from .models import CreditCourse


admin.site.register(CreditCourse)
