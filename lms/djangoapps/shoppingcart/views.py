import logging
import datetime
import pytz
from django.conf import settings
from django.contrib.auth.models import Group
from django.http import (HttpResponse, HttpResponseRedirect, HttpResponseNotFound,
    HttpResponseBadRequest, HttpResponseForbidden, Http404)
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from shoppingcart.reports import RefundReport, ItemizedPurchaseReport, UniversityRevenueShareReport, CertificateStatusReport
# TODO: processors shouldn't be exposed here. Abstract flow to work with everything and interface with processors/__init__.py
from shoppingcart.processors.Paypal import create_payment, execute_payment
from student.models import CourseEnrollment
from .exceptions import ItemAlreadyInCartException, AlreadyEnrolledInCourseException, CourseDoesNotExistException, ReportTypeDoesNotExistException, CouponAlreadyExistException, ItemDoesNotExistAgainstCouponException
from .models import Order, PaidCourseRegistration, OrderItem, Coupon, CouponRedemption
from .processors import process_postpay_callback, render_purchase_form_html
import json

log = logging.getLogger("shoppingcart")

EVENT_NAME_USER_UPGRADED = 'edx.course.enrollment.upgrade.succeeded'

REPORT_TYPES = [
    ("refund_report", RefundReport),
    ("itemized_purchase_report", ItemizedPurchaseReport),
    ("university_revenue_share", UniversityRevenueShareReport),
    ("certificate_status", CertificateStatusReport),
]


def initialize_report(report_type, start_date, end_date, start_letter=None, end_letter=None):
    """
    Creates the appropriate type of Report object based on the string report_type.
    """
    for item in REPORT_TYPES:
        if report_type in item:
            return item[1](start_date, end_date, start_letter, end_letter)
    raise ReportTypeDoesNotExistException

@require_POST
def add_course_to_cart(request, course_id):
    """
    Adds course specified by course_id to the cart.  The model function add_to_order does all the
    heavy lifting (logging, error checking, etc)
    """

    assert isinstance(course_id, basestring)
    if not request.user.is_authenticated():
        log.info("Anon user trying to add course {} to cart".format(course_id))
        return HttpResponseForbidden(_('You must be logged-in to add to a shopping cart'))
    cart = Order.get_cart_for_user(request.user)
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    # All logging from here handled by the model
    try:
        PaidCourseRegistration.add_to_order(cart, course_key)
    except CourseDoesNotExistException:
        return HttpResponseNotFound(_('The course you requested does not exist.'))
    except ItemAlreadyInCartException:
        return HttpResponseBadRequest(_('The course {0} is already in your cart.'.format(course_id)))
    except AlreadyEnrolledInCourseException:
        return HttpResponseBadRequest(_('You are already registered in course {0}.'.format(course_id)))
    return HttpResponse(_("Course added to cart."))


@login_required
def show_cart(request):
    cart = Order.get_cart_for_user(request.user)
    total_cost = cart.total_cost
    cart_items = cart.orderitem_set.all()

    # add the request protocol, domain, and port to the cart object so that any specific
    # CC_PROCESSOR implementation can construct callback URLs, if necessary
    cart.context = {
        'request_domain': '{0}://{1}'.format(
            'https' if request.is_secure() else 'http',
            request.get_host()
        )
    }

    form_html = render_purchase_form_html(cart)
    return render_to_response("shoppingcart/list.html",
                              {'shoppingcart_items': cart_items,
                               'amount': total_cost,
                               'form_html': form_html,
                               })


@login_required
def clear_cart(request):
    cart = Order.get_cart_for_user(request.user)
    cart.clear()
    coupon_redemption = CouponRedemption.objects.filter(user=request.user, order=cart.id)
    if coupon_redemption:
        coupon_redemption.delete()
        log.info('Coupon redemption entry removed for user {0} for order {1}'.format(request.user, cart.id))

    return HttpResponse('Cleared')


@login_required
def remove_item(request):
    item_id = request.REQUEST.get('id', '-1')
    try:
        item = OrderItem.objects.get(id=item_id, status='cart')
        if item.user == request.user:
            order_item_course_id = None
            if hasattr(item, 'paidcourseregistration'):
                order_item_course_id = item.paidcourseregistration.course_id
            item.delete()
            log.info('order item {0} removed for user {1}'.format(item_id, request.user))
            try:
                coupon_redemption = CouponRedemption.objects.get(user=request.user, order=item.order_id)
                if order_item_course_id == coupon_redemption.coupon.course_id:
                    coupon_redemption.delete()
                    log.info('Coupon "{0}" redemption entry removed for user "{1}" for order item "{2}"'
                             .format(coupon_redemption.coupon.code, request.user, item_id))
            except CouponRedemption.DoesNotExist:
                log.debug('Coupon redemption does not exist for order item id={0}.'.format(item_id))
    except OrderItem.DoesNotExist:
        log.exception('Cannot remove cart OrderItem id={0}. DoesNotExist or item is already purchased'.format(item_id))
    return HttpResponse('OK')


@login_required
def use_coupon(request):
    """
    This method generate discount against valid coupon code and save its entry into coupon redemption table
    """
    coupon_code = request.POST["coupon_code"]
    try:
        coupon = Coupon.objects.get(code=coupon_code)
    except Coupon.DoesNotExist:
        return HttpResponseNotFound(_("Discount does not exist against coupon '{0}'.".format(coupon_code)))

    if coupon.is_active:
        try:
            cart = Order.get_cart_for_user(request.user)
            CouponRedemption.add_coupon_redemption(coupon, cart)
        except CouponAlreadyExistException:
            return HttpResponseBadRequest(_("Coupon '{0}' already used.".format(coupon_code)))
        except ItemDoesNotExistAgainstCouponException:
            return HttpResponseNotFound(_("Coupon '{0}' is not valid for any course in the shopping cart.".format(coupon_code)))

        response = HttpResponse(json.dumps({'response': 'success'}), content_type="application/json")
        return response
    else:
        return HttpResponseBadRequest(_("Coupon '{0}' is inactive.".format(coupon_code)))

@csrf_exempt
@require_POST
def paypal_checkout(request):
    """
    A view for the paypal checkout form

    Takes one of two paths:

    - Paypal -> postpay_callback
    - Renders an error page

    TODO: Figure out how to abstract/move this into Paypal.py
    Need to be able to handle this and other payment flows.
    """
    # create payment and redirect user
    redirect_url = None
    payment = create_payment(request.REQUEST)

    # putting order number into session so process_postpay_callback can see it.
    # this is necessary because we need the order num to redirect user to receipt
    # TODO: figure out how to get paypal to send back order number, etc.
    order_num = request.REQUEST['orderNumber']
    request.REQUEST["order_num"] = order_num

    if payment.success():
        for link in payment.links:
            if link.method == "REDIRECT":
                redirect_url = link.href
                log.info("Redirect for approval: {}".format(redirect_url))
                return HttpResponseRedirect(redirect_url)
    else:
        # we don't want to fail to generate the error page so if
        # things go terribly wrong the user will be redirected
        # to an error page with N/A's
        order_num = request.REQUEST.get('orderNumber', 'N/A')
        # TODO: Generate error_html for paypal errors
        error_html = request.REQUEST.get('error_html', "<h3> Sorry, that's all we know.")
        return render_to_response('shoppingcart/error.html',
                                  {
                                      'order': order_num,
                                      'error_html': error_html
                                  }
        )


@csrf_exempt
# @require_POST
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
    params = request.REQUEST
    result = process_postpay_callback(params)
    if result['success']:
        return HttpResponseRedirect(reverse('shoppingcart.views.show_receipt', args=[result['order'].id]))
    else:
        return render_to_response('shoppingcart/error.html', {'order': result['order'],
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

    order_items = OrderItem.objects.filter(order=order).select_subclasses()
    any_refunds = any(i.status == "refunded" for i in order_items)
    receipt_template = 'shoppingcart/receipt.html'
    __, instructions = order.generate_receipt_instructions()
    # we want to have the ability to override the default receipt page when
    # there is only one item in the order
    context = {
        'order': order,
        'order_items': order_items,
        'any_refunds': any_refunds,
        'instructions': instructions,
    }

    if order_items.count() == 1:
        receipt_template = order_items[0].single_item_receipt_template
        context.update(order_items[0].single_item_receipt_context)

    # Only orders where order_items.count() == 1 might be attempting to upgrade
    attempting_upgrade = request.session.get('attempting_upgrade', False)
    if attempting_upgrade:
        course_enrollment = CourseEnrollment.get_or_create_enrollment(request.user, order_items[0].course_id)
        course_enrollment.emit_event(EVENT_NAME_USER_UPGRADED)
        request.session['attempting_upgrade'] = False

    return render_to_response(receipt_template, context)


def _can_download_report(user):
    """
    Tests if the user can download the payments report, based on membership in a group whose name is determined
     in settings.  If the group does not exist, denies all access
    """
    try:
        access_group = Group.objects.get(name=settings.PAYMENT_REPORT_GENERATOR_GROUP)
    except Group.DoesNotExist:
        return False
    return access_group in user.groups.all()


def _get_date_from_str(date_input):
    """
    Gets date from the date input string.  Lets the ValueError raised by invalid strings be processed by the caller
    """
    return datetime.datetime.strptime(date_input.strip(), "%Y-%m-%d").replace(tzinfo=pytz.UTC)


def _render_report_form(start_str, end_str, start_letter, end_letter, report_type, total_count_error=False, date_fmt_error=False):
    """
    Helper function that renders the purchase form.  Reduces repetition
    """
    context = {
        'total_count_error': total_count_error,
        'date_fmt_error': date_fmt_error,
        'start_date': start_str,
        'end_date': end_str,
        'start_letter': start_letter,
        'end_letter': end_letter,
        'requested_report': report_type,
    }
    return render_to_response('shoppingcart/download_report.html', context)


@login_required
def csv_report(request):
    """
    Downloads csv reporting of orderitems
    """
    if not _can_download_report(request.user):
        return HttpResponseForbidden(_('You do not have permission to view this page.'))

    if request.method == 'POST':
        start_date = request.POST.get('start_date', '')
        end_date = request.POST.get('end_date', '')
        start_letter = request.POST.get('start_letter', '')
        end_letter = request.POST.get('end_letter', '')
        report_type = request.POST.get('requested_report', '')
        try:
            start_date = _get_date_from_str(start_date) + datetime.timedelta(days=0)
            end_date = _get_date_from_str(end_date) + datetime.timedelta(days=1)
        except ValueError:
            # Error case: there was a badly formatted user-input date string
            return _render_report_form(start_date, end_date, start_letter, end_letter, report_type, date_fmt_error=True)

        report = initialize_report(report_type, start_date, end_date, start_letter, end_letter)
        items = report.rows()

        response = HttpResponse(mimetype='text/csv')
        filename = "purchases_report_{}.csv".format(datetime.datetime.now(pytz.UTC).strftime("%Y-%m-%d-%H-%M-%S"))
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        report.write_csv(response)
        return response

    elif request.method == 'GET':
        end_date = datetime.datetime.now(pytz.UTC)
        start_date = end_date - datetime.timedelta(days=30)
        start_letter = ""
        end_letter = ""
        return _render_report_form(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), start_letter, end_letter, report_type="")

    else:
        return HttpResponseBadRequest("HTTP Method Not Supported")
