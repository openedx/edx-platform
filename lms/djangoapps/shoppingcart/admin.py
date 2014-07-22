"""
Allows django admin site to add PaidCourseRegistrationAnnotations
"""
from ratelimitbackend import admin
from shoppingcart.models import PaidCourseRegistrationAnnotation, Coupon


class SoftDeleteCouponAdmin(admin.ModelAdmin):
    """
    Admin for the Coupon table.
    soft-delete on the coupons
    """
    fields = ('code', 'description', 'course_id', 'percentage_discount', 'created_by', 'created_at', 'is_active')
    raw_id_fields = ("created_by",)
    readonly_fields = ('created_at',)
    actions = ['really_delete_selected']

    def queryset(self, request):
        """ Returns a QuerySet of all model instances that can be edited by the
        admin site. This is used by changelist_view. """
        # Default: qs = self.model._default_manager.get_active_coupons_query_set()
        # Queryset with all the coupons including the soft-deletes: qs = self.model._default_manager.get_query_set()
        query_string = self.model._default_manager.get_active_coupons_query_set()  # pylint: disable=W0212
        return query_string

    def get_actions(self, request):
        actions = super(SoftDeleteCouponAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def really_delete_selected(self, request, queryset):
        """override the default behavior of selected delete method"""
        for obj in queryset:
            obj.is_active = False
            obj.save()

        if queryset.count() == 1:
            message_bit = "1 coupon entry was"
        else:
            message_bit = "%s coupon entries were" % queryset.count()
        self.message_user(request, "%s successfully deleted." % message_bit)

    def delete_model(self, request, obj):
        """override the default behavior of single instance of model delete method"""
        obj.is_active = False
        obj.save()

    really_delete_selected.short_description = "Delete s selected entries"

admin.site.register(PaidCourseRegistrationAnnotation)
admin.site.register(Coupon, SoftDeleteCouponAdmin)
