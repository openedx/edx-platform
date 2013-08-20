import logging
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound, HttpResponseForbidden, Http404
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from student.models import CourseEnrollment
from xmodule.modulestore.exceptions import ItemNotFoundError
from mitxmako.shortcuts import render_to_response
from .models import *
from .processors import process_postpay_callback, render_purchase_form_html

log = logging.getLogger("shoppingcart")

def test(request, course_id):
    item1 = PaidCourseRegistration(course_id, 200)
    item1.purchased_callback(request.user.id)
    return HttpResponse('OK')


def add_course_to_cart(request, course_id):
    if not request.user.is_authenticated():
        return HttpResponseForbidden(_('You must be logged-in to add to a shopping cart'))
    cart = Order.get_cart_for_user(request.user)
    if PaidCourseRegistration.part_of_order(cart, course_id):
        return HttpResponseNotFound(_('The course {0} is already in your cart.'.format(course_id)))
    if CourseEnrollment.is_enrolled(user=request.user, course_id=course_id):
        return HttpResponseNotFound(_('You are already registered in course {0}.'.format(course_id)))
    try:
        PaidCourseRegistration.add_to_order(cart, course_id)
    except ItemNotFoundError:
        return HttpResponseNotFound(_('The course you requested does not exist.'))
    if request.method == 'GET':
        return HttpResponseRedirect(reverse('shoppingcart.views.show_cart'))
    return HttpResponse(_("Course added to cart."))


@login_required
def register_for_verified_cert(request, course_id):
    cart = Order.get_cart_for_user(request.user)
    CertificateItem.add_to_order(cart, course_id, 30, 'verified')
    return HttpResponse("Added")

@login_required
def show_cart(request):
    cart = Order.get_cart_for_user(request.user)
    total_cost = cart.total_cost
    amount = "{0:0.2f}".format(total_cost)
    cart_items = cart.orderitem_set.all()
    form_html = render_purchase_form_html(cart, request.user)
    return render_to_response("shoppingcart/list.html",
                              {'shoppingcart_items': cart_items,
                               'amount': amount,
                               'form_html': form_html,
                               })

@login_required
def clear_cart(request):
    cart = Order.get_cart_for_user(request.user)
    cart.clear()
    return HttpResponse('Cleared')

@login_required
def remove_item(request):
    item_id = request.REQUEST.get('id', '-1')
    try:
        item = OrderItem.objects.get(id=item_id, status='cart')
        if item.user == request.user:
            item.delete()
    except OrderItem.DoesNotExist:
        log.exception('Cannot remove cart OrderItem id={0}. DoesNotExist or item is already purchased'.format(item_id))
    return HttpResponse('OK')

@csrf_exempt
def postpay_callback(request):
    """
    Receives the POST-back from processor.
    Mainly this calls the processor-specific code to check if the payment was accepted, and to record the order
    if it was, and to generate an error page.
    If successful this function should have the side effect of changing the "cart" into a full "order" in the DB.
    The cart can then render a success page which links to receipt pages.
    If unsuccessful the order will be left untouched and HTML messages giving more detailed error info will be
    returned.
    """
    result = process_postpay_callback(request)
    if result['success']:
        return HttpResponseRedirect(reverse('shoppingcart.views.show_receipt', args=[result['order'].id]))
    else:
        return render_to_response('shoppingcart.processor_error.html', {'order':result['order'],
                                                                        'error_html': result['error_html']})

@login_required
def show_receipt(request, ordernum):
    """
    Displays a receipt for a particular order.
    404 if order is not yet purchased or request.user != order.user
    """
    try:
        order = Order.objects.get(id=ordernum)
    except Order.DoesNotExist:
        raise Http404('Order not found!')

    if order.user != request.user or order.status != 'purchased':
        raise Http404('Order not found!')

    order_items = order.orderitem_set.all()
    any_refunds = "refunded" in [i.status for i in order_items]
    return render_to_response('shoppingcart/receipt.html', {'order': order,
                                                            'order_items': order_items,
                                                            'any_refunds': any_refunds})
