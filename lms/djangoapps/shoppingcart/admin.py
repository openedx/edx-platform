"""
Allows django admin site to add PaidCourseRegistrationAnnotations
"""
from ratelimitbackend import admin
from shoppingcart.models import PaidCourseRegistrationAnnotation

admin.site.register(PaidCourseRegistrationAnnotation)
