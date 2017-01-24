"""
API for for getting information about the user's shopping cart.
"""
from django.core.urlresolvers import reverse
from xmodule.modulestore.django import ModuleI18nService
from shoppingcart.models import OrderItem


def order_history(user, **kwargs):
    """
    Returns the list of previously purchased orders for a user. Only the orders with
    PaidCourseRegistration and CourseRegCodeItem are returned.
    Params:
     course_org_filter: Current Microsite's ORG.
     org_filter_out_set: A list of all other Microsites' ORGs.
    """
    course_org_filter = kwargs['course_org_filter'] if 'course_org_filter' in kwargs else None
    org_filter_out_set = kwargs['org_filter_out_set'] if 'org_filter_out_set' in kwargs else []

    order_history_list = []
    purchased_order_items = OrderItem.objects.filter(user=user, status='purchased').select_subclasses().order_by('-fulfilled_time')
    for order_item in purchased_order_items:
        # Avoid repeated entries for the same order id.
        if order_item.order.id not in [item['order_id'] for item in order_history_list]:
            # If we are in a Microsite, then include the orders having courses attributed (by ORG) to that Microsite.
            # Conversely, if we are not in a Microsite, then include the orders having courses
            # not attributed (by ORG) to any Microsite.
            order_item_course_id = getattr(order_item, 'course_id', None)
            if order_item_course_id:
                if (course_org_filter and course_org_filter == order_item_course_id.org) or \
                        (course_org_filter is None and order_item_course_id.org not in org_filter_out_set):
                    order_history_list.append({
                        'order_id': order_item.order.id,
                        'receipt_url': reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': order_item.order.id}),
                        'order_date': ModuleI18nService().strftime(order_item.order.purchase_time, 'SHORT_DATE')
                    })
    return order_history_list
