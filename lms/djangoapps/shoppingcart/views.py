import logging

from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response
from .models import *
from .processors import verify, render_purchase_form_html

log = logging.getLogger("shoppingcart")

def test(request, course_id):
    item1 = PaidCourseRegistration(course_id, 200)
    item1.purchased_callback(request.user.id)
    return HttpResponse('OK')

@login_required
def purchased(request):
    #verify() -- signatures, total cost match up, etc.  Need error handling code (
    # If verify fails probaly need to display a contact email/number)
    cart = Order.get_cart_for_user(request.user)
    cart.purchase()
    return HttpResponseRedirect('/')

@login_required
def add_course_to_cart(request, course_id):
    cart = Order.get_cart_for_user(request.user)
    # TODO: Catch 500 here for course that does not exist, period
    PaidCourseRegistration.add_to_order(cart, course_id, 200)
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
    cart.orderitem_set.all().delete()
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
def receipt(request):
    """
    Receives the POST-back from processor and performs the validation and displays a receipt
    and does some other stuff
    """
    if verify(request.POST.dict()):
        return HttpResponse("Validated")
    else:
        return HttpResponse("Not Validated")

