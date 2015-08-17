"""Django admin interface for the shopping cart models. """
from ratelimitbackend import admin
from shoppingcart.models import (
    PaidCourseRegistrationAnnotation,
    Coupon,
    DonationConfiguration,
    Invoice,
    CourseRegistrationCodeInvoiceItem,
    InvoiceTransaction
)


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
        query_string = self.model._default_manager.get_active_coupons_query_set()  # pylint: disable=protected-access
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


class CourseRegistrationCodeInvoiceItemInline(admin.StackedInline):
    """Admin for course registration code invoice items.

    Displayed inline within the invoice admin UI.
    """
    model = CourseRegistrationCodeInvoiceItem
    extra = 0
    can_delete = False
    readonly_fields = (
        'qty',
        'unit_price',
        'currency',
        'course_id',
    )

    def has_add_permission(self, request):
        return False


class InvoiceTransactionInline(admin.StackedInline):
    """Admin for invoice transactions.

    Displayed inline within the invoice admin UI.
    """
    model = InvoiceTransaction
    extra = 0
    readonly_fields = (
        'created',
        'modified',
        'created_by',
        'last_modified_by'
    )


class InvoiceAdmin(admin.ModelAdmin):
    """Admin for invoices.

    This is intended for the internal finance team
    to be able to view and update invoice information,
    including payments and refunds.

    """
    date_hierarchy = 'created'
    can_delete = False
    readonly_fields = ('created', 'modified')
    search_fields = (
        'internal_reference',
        'customer_reference_number',
        'company_name',
    )
    fieldsets = (
        (
            None, {
                'fields': (
                    'internal_reference',
                    'customer_reference_number',
                    'created',
                    'modified',
                )
            }
        ),
        (
            'Billing Information', {
                'fields': (
                    'company_name',
                    'company_contact_name',
                    'company_contact_email',
                    'recipient_name',
                    'recipient_email',
                    'address_line_1',
                    'address_line_2',
                    'address_line_3',
                    'city',
                    'state',
                    'zip',
                    'country'
                )
            }
        )
    )
    readonly_fields = (
        'internal_reference',
        'customer_reference_number',
        'created',
        'modified',
        'company_name',
        'company_contact_name',
        'company_contact_email',
        'recipient_name',
        'recipient_email',
        'address_line_1',
        'address_line_2',
        'address_line_3',
        'city',
        'state',
        'zip',
        'country'
    )
    inlines = [
        CourseRegistrationCodeInvoiceItemInline,
        InvoiceTransactionInline
    ]

    def save_formset(self, request, form, formset, change):
        """Save the user who created and modified invoice transactions. """
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, InvoiceTransaction):
                if not hasattr(instance, 'created_by'):
                    instance.created_by = request.user
                instance.last_modified_by = request.user
                instance.save()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(PaidCourseRegistrationAnnotation)
admin.site.register(Coupon, SoftDeleteCouponAdmin)
admin.site.register(DonationConfiguration)
admin.site.register(Invoice, InvoiceAdmin)
