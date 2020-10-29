"""
API for for getting information about the user's shopping cart.
"""


from django.urls import reverse

from shoppingcart.models import OrderItem
from xmodule.modulestore.django import ModuleI18nService


def order_history(user, **kwargs):
    """
    Returns the list of previously purchased orders for a user. Only the orders with
    PaidCourseRegistration and CourseRegCodeItem are returned.
    Params:
     course_org_filter: A list of the current Site's orgs.
     org_filter_out_set: A list of all other Sites' orgs.
    """
    course_org_filter = kwargs['course_org_filter'] if 'course_org_filter' in kwargs else None
    org_filter_out_set = kwargs['org_filter_out_set'] if 'org_filter_out_set' in kwargs else []

    order_history_list = []
    purchased_order_items = OrderItem.objects.filter(user=user, status='purchased').select_subclasses().order_by('-fulfilled_time')
    for order_item in purchased_order_items:
        # Avoid repeated entries for the same order id.
        if order_item.order.id not in [item['order_id'] for item in order_history_list]:
            order_item_course_id = getattr(order_item, 'course_id', None)
            if order_item_course_id:
                if (course_org_filter and order_item_course_id.org in course_org_filter) or \
                        (course_org_filter is None and order_item_course_id.org not in org_filter_out_set):
                    order_history_list.append({
                        'order_id': order_item.order.id,
                        'receipt_url': reverse('shoppingcart.views.show_receipt', kwargs={'ordernum': order_item.order.id}),
                        'order_date': ModuleI18nService().strftime(order_item.order.purchase_time, 'SHORT_DATE')
                    })
    return order_history_list
