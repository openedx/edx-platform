""" Models for the shopping cart and assorted purchase types """

from collections import namedtuple
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
import json
import analytics
from io import BytesIO
from django.db.models import Q, F
import pytz
import logging
import smtplib
import StringIO
import csv
from boto.exception import BotoServerError  # this is a super-class of SESError and catches connection errors
from django.dispatch import receiver
from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _, ugettext_lazy
from django.db import transaction
from django.db.models import Sum, Count
from django.db.models.signals import post_save, post_delete

from django.core.urlresolvers import reverse
from model_utils.managers import InheritanceManager
from model_utils.models import TimeStampedModel
from django.core.mail.message import EmailMessage
from xmodule.modulestore.django import modulestore
from eventtracking import tracker

from courseware.courses import get_course_by_id
from config_models.models import ConfigurationModel
from course_modes.models import CourseMode
from edxmako.shortcuts import render_to_string
from student.models import CourseEnrollment, UNENROLL_DONE
from util.query import use_read_replica_if_available
from xmodule_django.models import CourseKeyField
from .exceptions import (
    InvalidCartItem,
    PurchasedCallbackException,
    ItemAlreadyInCartException,
    AlreadyEnrolledInCourseException,
    CourseDoesNotExistException,
    MultipleCouponsNotAllowedException,
    InvalidStatusToRetire,
    UnexpectedOrderItemStatus,
    ItemNotFoundInCartException
)
from microsite_configuration import microsite
from shoppingcart.pdf import PDFInvoice


log = logging.getLogger("shoppingcart")

ORDER_STATUSES = (
    # The user is selecting what he/she wants to purchase.
    ('cart', 'cart'),

    # The user has been sent to the external payment processor.
    # At this point, the order should NOT be modified.
    # If the user returns to the payment flow, he/she will start a new order.
    ('paying', 'paying'),

    # The user has successfully purchased the items in the order.
    ('purchased', 'purchased'),

    # The user's order has been refunded.
    ('refunded', 'refunded'),

    # The user's order went through, but the order was erroneously left
    # in 'cart'.
    ('defunct-cart', 'defunct-cart'),

    # The user's order went through, but the order was erroneously left
    # in 'paying'.
    ('defunct-paying', 'defunct-paying'),
)

# maps order statuses to their defunct states
ORDER_STATUS_MAP = {
    'cart': 'defunct-cart',
    'paying': 'defunct-paying',
}

# we need a tuple to represent the primary key of various OrderItem subclasses
OrderItemSubclassPK = namedtuple('OrderItemSubclassPK', ['cls', 'pk'])


class OrderTypes(object):
    """
    This class specify purchase OrderTypes.
    """
    PERSONAL = 'personal'
    BUSINESS = 'business'

    ORDER_TYPES = (
        (PERSONAL, 'personal'),
        (BUSINESS, 'business'),
    )


class Order(models.Model):
    """
    This is the model for an order.  Before purchase, an Order and its related OrderItems are used
    as the shopping cart.
    FOR ANY USER, THERE SHOULD ONLY EVER BE ZERO OR ONE ORDER WITH STATUS='cart'.
    """
    class Meta(object):
        app_label = "shoppingcart"

    user = models.ForeignKey(User, db_index=True)
    currency = models.CharField(default="usd", max_length=8)  # lower case ISO currency codes
    status = models.CharField(max_length=32, default='cart', choices=ORDER_STATUSES)
    purchase_time = models.DateTimeField(null=True, blank=True)
    refunded_time = models.DateTimeField(null=True, blank=True)
    # Now we store data needed to generate a reasonable receipt
    # These fields only make sense after the purchase
    bill_to_first = models.CharField(max_length=64, blank=True)
    bill_to_last = models.CharField(max_length=64, blank=True)
    bill_to_street1 = models.CharField(max_length=128, blank=True)
    bill_to_street2 = models.CharField(max_length=128, blank=True)
    bill_to_city = models.CharField(max_length=64, blank=True)
    bill_to_state = models.CharField(max_length=8, blank=True)
    bill_to_postalcode = models.CharField(max_length=16, blank=True)
    bill_to_country = models.CharField(max_length=64, blank=True)
    bill_to_ccnum = models.CharField(max_length=8, blank=True)  # last 4 digits
    bill_to_cardtype = models.CharField(max_length=32, blank=True)
    # a JSON dump of the CC processor response, for completeness
    processor_reply_dump = models.TextField(blank=True)

    # bulk purchase registration code workflow billing details
    company_name = models.CharField(max_length=255, null=True, blank=True)
    company_contact_name = models.CharField(max_length=255, null=True, blank=True)
    company_contact_email = models.CharField(max_length=255, null=True, blank=True)
    recipient_name = models.CharField(max_length=255, null=True, blank=True)
    recipient_email = models.CharField(max_length=255, null=True, blank=True)
    customer_reference_number = models.CharField(max_length=63, null=True, blank=True)
    order_type = models.CharField(max_length=32, default='personal', choices=OrderTypes.ORDER_TYPES)

    @classmethod
    def get_cart_for_user(cls, user):
        """
        Always use this to preserve the property that at most 1 order per user has status = 'cart'
        """
        # find the newest element in the db
        try:
            cart_order = cls.objects.filter(user=user, status='cart').order_by('-id')[:1].get()
        except ObjectDoesNotExist:
            # if nothing exists in the database, create a new cart
            cart_order, _created = cls.objects.get_or_create(user=user, status='cart')
        return cart_order

    @classmethod
    def does_user_have_cart(cls, user):
        """
        Returns a boolean whether a shopping cart (Order) exists for the specified user
        """
        return cls.objects.filter(user=user, status='cart').exists()

    @classmethod
    def user_cart_has_items(cls, user, item_types=None):
        """
        Returns true if the user (anonymous user ok) has
        a cart with items in it.  (Which means it should be displayed.
        If a item_type is passed in, then we check to see if the cart has at least one of
        those types of OrderItems
        """
        if not user.is_authenticated():
            return False
        cart = cls.get_cart_for_user(user)

        if not item_types:
            # check to see if the cart has at least some item in it
            return cart.has_items()
        else:
            # if the caller is explicitly asking to check for particular types
            for item_type in item_types:
                if cart.has_items(item_type):
                    return True

        return False

    @classmethod
    def remove_cart_item_from_order(cls, item, user):
        """
        Removes the item from the cart if the item.order.status == 'cart'.
        Also removes any code redemption associated with the order_item
        """
        if item.order.status == 'cart':
            log.info("order item %s removed for user %s", str(item.id), user)
            item.delete()
            # remove any redemption entry associated with the item
            CouponRedemption.remove_code_redemption_from_item(item, user)

    @property
    def total_cost(self):
        """
        Return the total cost of the cart.  If the order has been purchased, returns total of
        all purchased and not refunded items.
        """
        return sum(i.line_cost for i in self.orderitem_set.filter(status=self.status))

    def has_items(self, item_type=None):
        """
        Does the cart have any items in it?
        If an item_type is passed in then we check to see if there are any items of that class type
        """
        if not item_type:
            return self.orderitem_set.exists()
        else:
            items = self.orderitem_set.all().select_subclasses()
            for item in items:
                if isinstance(item, item_type):
                    return True
            return False

    def reset_cart_items_prices(self):
        """
        Reset the items price state in the user cart
        """
        for item in self.orderitem_set.all():
            if item.is_discounted:
                item.unit_cost = item.list_price
                item.save()

    def clear(self):
        """
        Clear out all the items in the cart
        """
        self.orderitem_set.all().delete()

    @transaction.atomic
    def start_purchase(self):
        """
        Start the purchase process.  This will set the order status to "paying",
        at which point it should no longer be modified.

        Future calls to `Order.get_cart_for_user()` will filter out orders with
        status "paying", effectively creating a new (empty) cart.
        """
        if self.status == 'cart':
            self.status = 'paying'
            self.save()

            for item in OrderItem.objects.filter(order=self).select_subclasses():
                item.start_purchase()

    def update_order_type(self):
        """
        updating order type. This method wil inspect the quantity associated with the OrderItem.
        In the application, it is implied that when qty > 1, then the user is to purchase
        'RegistrationCodes' which are randomly generated strings that users can distribute to
        others in order for them to enroll in paywalled courses.

        The UI/UX may change in the future to make the switching between PaidCourseRegistration
        and CourseRegCodeItems a more explicit UI gesture from the purchaser
        """
        cart_items = self.orderitem_set.all()
        is_order_type_business = False
        for cart_item in cart_items:
            if cart_item.qty > 1:
                is_order_type_business = True

        items_to_delete = []
        old_to_new_id_map = []
        if is_order_type_business:
            for cart_item in cart_items:
                if hasattr(cart_item, 'paidcourseregistration'):
                    course_reg_code_item = CourseRegCodeItem.add_to_order(self, cart_item.paidcourseregistration.course_id, cart_item.qty)
                    # update the discounted prices if coupon redemption applied
                    course_reg_code_item.list_price = cart_item.list_price
                    course_reg_code_item.unit_cost = cart_item.unit_cost
                    course_reg_code_item.save()
                    items_to_delete.append(cart_item)
                    old_to_new_id_map.append({"oldId": cart_item.id, "newId": course_reg_code_item.id})
        else:
            for cart_item in cart_items:
                if hasattr(cart_item, 'courseregcodeitem'):
                    paid_course_registration = PaidCourseRegistration.add_to_order(self, cart_item.courseregcodeitem.course_id)
                    # update the discounted prices if coupon redemption applied
                    paid_course_registration.list_price = cart_item.list_price
                    paid_course_registration.unit_cost = cart_item.unit_cost
                    paid_course_registration.save()
                    items_to_delete.append(cart_item)
                    old_to_new_id_map.append({"oldId": cart_item.id, "newId": paid_course_registration.id})

        for item in items_to_delete:
            item.delete()

        self.order_type = OrderTypes.BUSINESS if is_order_type_business else OrderTypes.PERSONAL
        self.save()
        return old_to_new_id_map

    def generate_pdf_receipt(self, order_items):
        """
        Generates the pdf receipt for the given order_items
        and returns the pdf_buffer.
        """
        items_data = []
        for item in order_items:
            item_total = item.qty * item.unit_cost
            items_data.append({
                'item_description': item.pdf_receipt_display_name,
                'quantity': item.qty,
                'list_price': item.get_list_price(),
                'discount': item.get_list_price() - item.unit_cost,
                'item_total': item_total
            })
        pdf_buffer = BytesIO()

        PDFInvoice(
            items_data=items_data,
            item_id=str(self.id),
            date=self.purchase_time,
            is_invoice=False,
            total_cost=self.total_cost,
            payment_received=self.total_cost,
            balance=0
        ).generate_pdf(pdf_buffer)
        return pdf_buffer

    def generate_registration_codes_csv(self, orderitems, site_name):
        """
        this function generates the csv file
        """
        course_info = []
        csv_file = StringIO.StringIO()
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Course Name', 'Registration Code', 'URL'])
        for item in orderitems:
            course_id = item.course_id
            course = get_course_by_id(item.course_id, depth=0)
            registration_codes = CourseRegistrationCode.objects.filter(course_id=course_id, order=self)
            course_info.append((course.display_name, ' (' + course.start_datetime_text() + '-' + course.end_datetime_text() + ')'))
            for registration_code in registration_codes:
                redemption_url = reverse('register_code_redemption', args=[registration_code.code])
                url = '{base_url}{redemption_url}'.format(base_url=site_name, redemption_url=redemption_url)
                csv_writer.writerow([unicode(course.display_name).encode("utf-8"), registration_code.code, url])

        return csv_file, course_info

    def send_confirmation_emails(self, orderitems, is_order_type_business, csv_file, pdf_file, site_name, courses_info):
        """
        send confirmation e-mail
        """
        recipient_list = [(self.user.username, self.user.email, 'user')]  # pylint: disable=no-member
        if self.company_contact_email:
            recipient_list.append((self.company_contact_name, self.company_contact_email, 'company_contact'))
        joined_course_names = ""
        if self.recipient_email:
            recipient_list.append((self.recipient_name, self.recipient_email, 'email_recipient'))
            courses_names_with_dates = [course_info[0] + course_info[1] for course_info in courses_info]
            joined_course_names = " " + ", ".join(courses_names_with_dates)

        if not is_order_type_business:
            subject = _("Order Payment Confirmation")
        else:
            subject = _('Confirmation and Registration Codes for the following courses: {course_name_list}').format(
                course_name_list=joined_course_names
            )

        dashboard_url = '{base_url}{dashboard}'.format(
            base_url=site_name,
            dashboard=reverse('dashboard')
        )
        try:
            from_address = microsite.get_value(
                'email_from_address',
                settings.PAYMENT_CONFIRM_EMAIL
            )
            # Send a unique email for each recipient. Don't put all email addresses in a single email.
            for recipient in recipient_list:
                message = render_to_string(
                    'emails/business_order_confirmation_email.txt' if is_order_type_business else 'emails/order_confirmation_email.txt',
                    {
                        'order': self,
                        'recipient_name': recipient[0],
                        'recipient_type': recipient[2],
                        'site_name': site_name,
                        'order_items': orderitems,
                        'course_names': ", ".join([course_info[0] for course_info in courses_info]),
                        'dashboard_url': dashboard_url,
                        'currency_symbol': settings.PAID_COURSE_REGISTRATION_CURRENCY[1],
                        'order_placed_by': '{username} ({email})'.format(
                            username=self.user.username, email=self.user.email
                        ),
                        'has_billing_info': settings.FEATURES['STORE_BILLING_INFO'],
                        'platform_name': microsite.get_value('platform_name', settings.PLATFORM_NAME),
                        'payment_support_email': microsite.get_value('payment_support_email', settings.PAYMENT_SUPPORT_EMAIL),
                        'payment_email_signature': microsite.get_value('payment_email_signature'),
                    }
                )
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=from_address,
                    to=[recipient[1]]
                )

                # Only the business order is HTML formatted. A single seat order confirmation is plain text.
                if is_order_type_business:
                    email.content_subtype = "html"

                if csv_file:
                    email.attach(u'RegistrationCodesRedemptionUrls.csv', csv_file.getvalue(), 'text/csv')
                if pdf_file is not None:
                    email.attach(u'Receipt.pdf', pdf_file.getvalue(), 'application/pdf')
                else:
                    file_buffer = StringIO.StringIO(_('pdf download unavailable right now, please contact support.'))
                    email.attach(u'pdf_not_available.txt', file_buffer.getvalue(), 'text/plain')
                email.send()
        except (smtplib.SMTPException, BotoServerError):  # sadly need to handle diff. mail backends individually
            log.error('Failed sending confirmation e-mail for order %d', self.id)

    def purchase(self, first='', last='', street1='', street2='', city='', state='', postalcode='',
                 country='', ccnum='', cardtype='', processor_reply_dump=''):
        """
        Call to mark this order as purchased.  Iterates through its OrderItems and calls
        their purchased_callback

        `first` - first name of person billed (e.g. John)
        `last` - last name of person billed (e.g. Smith)
        `street1` - first line of a street address of the billing address (e.g. 11 Cambridge Center)
        `street2` - second line of a street address of the billing address (e.g. Suite 101)
        `city` - city of the billing address (e.g. Cambridge)
        `state` - code of the state, province, or territory of the billing address (e.g. MA)
        `postalcode` - postal code of the billing address (e.g. 02142)
        `country` - country code of the billing address (e.g. US)
        `ccnum` - last 4 digits of the credit card number of the credit card billed (e.g. 1111)
        `cardtype` - 3-digit code representing the card type used (e.g. 001)
        `processor_reply_dump` - all the parameters returned by the processor

        """
        if self.status == 'purchased':
            log.error(
                u"`purchase` method called on order {}, but order is already purchased.".format(self.id)  # pylint: disable=no-member
            )
            return
        self.status = 'purchased'
        self.purchase_time = datetime.now(pytz.utc)
        self.bill_to_first = first
        self.bill_to_last = last
        self.bill_to_city = city
        self.bill_to_state = state
        self.bill_to_country = country
        self.bill_to_postalcode = postalcode
        if settings.FEATURES['STORE_BILLING_INFO']:
            self.bill_to_street1 = street1
            self.bill_to_street2 = street2
            self.bill_to_ccnum = ccnum
            self.bill_to_cardtype = cardtype
            self.processor_reply_dump = processor_reply_dump

        # save these changes on the order, then we can tell when we are in an
        # inconsistent state
        self.save()
        # this should return all of the objects with the correct types of the
        # subclasses
        orderitems = OrderItem.objects.filter(order=self).select_subclasses()
        site_name = microsite.get_value('SITE_NAME', settings.SITE_NAME)

        if self.order_type == OrderTypes.BUSINESS:
            self.update_order_type()

        for item in orderitems:
            item.purchase_item()

        csv_file = None
        courses_info = []
        if self.order_type == OrderTypes.BUSINESS:
            #
            # Generate the CSV file that contains all of the RegistrationCodes that have already been
            # generated when the purchase has transacted
            #
            csv_file, courses_info = self.generate_registration_codes_csv(orderitems, site_name)

        try:
            pdf_file = self.generate_pdf_receipt(orderitems)
        except Exception:  # pylint: disable=broad-except
            log.exception('Exception at creating pdf file.')
            pdf_file = None

        try:
            self.send_confirmation_emails(
                orderitems, self.order_type == OrderTypes.BUSINESS,
                csv_file, pdf_file, site_name, courses_info
            )
        except Exception:  # pylint: disable=broad-except
            # Catch all exceptions here, since the Django view implicitly
            # wraps this in a transaction.  If the order completes successfully,
            # we don't want to roll back just because we couldn't send
            # the confirmation email.
            log.exception('Error occurred while sending payment confirmation email')

        self._emit_order_event('Completed Order', orderitems)

    def refund(self):
        """
        Refund the given order. As of right now, this just marks the order as refunded.
        """
        self.status = 'refunded'
        self.save()
        orderitems = OrderItem.objects.filter(order=self).select_subclasses()
        self._emit_order_event('Refunded Order', orderitems)

    def _emit_order_event(self, event_name, orderitems):
        """
        Emit an analytics event with the given name for this Order. Will iterate over all associated
        OrderItems and add them as products in the event as well.

        """
        try:
            if settings.LMS_SEGMENT_KEY:
                tracking_context = tracker.get_tracker().resolve_context()
                analytics.track(self.user.id, event_name, {
                    'orderId': self.id,
                    'total': str(self.total_cost),
                    'currency': self.currency,
                    'products': [item.analytics_data() for item in orderitems]
                }, context={
                    'ip': tracking_context.get('ip'),
                    'Google Analytics': {
                        'clientId': tracking_context.get('client_id')
                    }
                })

        except Exception:  # pylint: disable=broad-except
            # Capturing all exceptions thrown while tracking analytics events. We do not want
            # an operation to fail because of an analytics event, so we will capture these
            # errors in the logs.
            log.exception(
                u'Unable to emit {event} event for user {user} and order {order}'.format(
                    event=event_name, user=self.user.id, order=self.id)
            )

    def add_billing_details(self, company_name='', company_contact_name='', company_contact_email='', recipient_name='',
                            recipient_email='', customer_reference_number=''):
        """
        This function is called after the user selects a purchase type of "Business" and
        is asked to enter the optional billing details. The billing details are updated
        for that order.

        company_name - Name of purchasing organization
        company_contact_name - Name of the key contact at the company the sale was made to
        company_contact_email - Email of the key contact at the company the sale was made to
        recipient_name - Name of the company should the invoice be sent to
        recipient_email - Email of the company should the invoice be sent to
        customer_reference_number - purchase order number of the organization associated with this Order
        """

        self.company_name = company_name
        self.company_contact_name = company_contact_name
        self.company_contact_email = company_contact_email
        self.recipient_name = recipient_name
        self.recipient_email = recipient_email
        self.customer_reference_number = customer_reference_number

        self.save()

    def generate_receipt_instructions(self):
        """
        Call to generate specific instructions for each item in the order.  This gets displayed on the receipt
        page, typically.  Instructions are something like "visit your dashboard to see your new courses".
        This will return two things in a pair.  The first will be a dict with keys=OrderItemSubclassPK corresponding
        to an OrderItem and values=a set of html instructions they generate.  The second will be a set of de-duped
        html instructions
        """
        instruction_set = set([])  # heh. not ia32 or alpha or sparc
        instruction_dict = {}
        order_items = OrderItem.objects.filter(order=self).select_subclasses()
        for item in order_items:
            item_pk_with_subclass, set_of_html = item.generate_receipt_instructions()
            instruction_dict[item_pk_with_subclass] = set_of_html
            instruction_set.update(set_of_html)
        return instruction_dict, instruction_set

    def retire(self):
        """
        Method to "retire" orders that have gone through to the payment service
        but have (erroneously) not had their statuses updated.
        This method only works on orders that satisfy the following conditions:
        1) the order status is either "cart" or "paying" (otherwise we raise
           an InvalidStatusToRetire error)
        2) the order's order item's statuses match the order's status (otherwise
           we throw an UnexpectedOrderItemStatus error)
        """
        # if an order is already retired, no-op:
        if self.status in ORDER_STATUS_MAP.values():
            return

        if self.status not in ORDER_STATUS_MAP.keys():
            raise InvalidStatusToRetire(
                "order status {order_status} is not 'paying' or 'cart'".format(
                    order_status=self.status
                )
            )

        for item in self.orderitem_set.all():
            if item.status != self.status:
                raise UnexpectedOrderItemStatus(
                    "order_item status is different from order status"
                )

        self.status = ORDER_STATUS_MAP[self.status]
        self.save()

        for item in self.orderitem_set.all():
            item.retire()

    def find_item_by_course_id(self, course_id):
        """
        course_id: Course id of the item to find
        Returns OrderItem from the Order given a course_id
        Raises exception ItemNotFoundException when the item
        having the given course_id is not present in the cart
        """
        cart_items = OrderItem.objects.filter(order=self).select_subclasses()
        found_items = []
        for item in cart_items:
            if getattr(item, 'course_id', None):
                if item.course_id == course_id:
                    found_items.append(item)
        if not found_items:
            raise ItemNotFoundInCartException
        return found_items


class OrderItem(TimeStampedModel):
    """
    This is the basic interface for order items.
    Order items are line items that fill up the shopping carts and orders.

    Each implementation of OrderItem should provide its own purchased_callback as
    a method.
    """
    class Meta(object):
        app_label = "shoppingcart"

    objects = InheritanceManager()
    order = models.ForeignKey(Order, db_index=True)
    # this is denormalized, but convenient for SQL queries for reports, etc. user should always be = order.user
    user = models.ForeignKey(User, db_index=True)
    # this is denormalized, but convenient for SQL queries for reports, etc. status should always be = order.status
    status = models.CharField(max_length=32, default='cart', choices=ORDER_STATUSES, db_index=True)
    qty = models.IntegerField(default=1)
    unit_cost = models.DecimalField(default=0.0, decimal_places=2, max_digits=30)
    list_price = models.DecimalField(decimal_places=2, max_digits=30, null=True)
    line_desc = models.CharField(default="Misc. Item", max_length=1024)
    currency = models.CharField(default="usd", max_length=8)  # lower case ISO currency codes
    fulfilled_time = models.DateTimeField(null=True, db_index=True)
    refund_requested_time = models.DateTimeField(null=True, db_index=True)
    service_fee = models.DecimalField(default=0.0, decimal_places=2, max_digits=30)
    # general purpose field, not user-visible.  Used for reporting
    report_comments = models.TextField(default="")

    @property
    def line_cost(self):
        """ Return the total cost of this OrderItem """
        return self.qty * self.unit_cost

    @classmethod
    def add_to_order(cls, order, *args, **kwargs):
        """
        A suggested convenience function for subclasses.

        NOTE: This does not add anything to the cart. That is left up to the
        subclasses to implement for themselves
        """
        # this is a validation step to verify that the currency of the item we
        # are adding is the same as the currency of the order we are adding it
        # to
        currency = kwargs.get('currency', 'usd')
        if order.currency != currency and order.orderitem_set.exists():
            raise InvalidCartItem(_("Trying to add a different currency into the cart"))

    @transaction.atomic
    def purchase_item(self):
        """
        This is basically a wrapper around purchased_callback that handles
        modifying the OrderItem itself
        """
        self.purchased_callback()
        self.status = 'purchased'
        self.fulfilled_time = datetime.now(pytz.utc)
        self.save()

    def start_purchase(self):
        """
        Start the purchase process.  This will set the order item status to "paying",
        at which point it should no longer be modified.
        """
        self.status = 'paying'
        self.save()

    def purchased_callback(self):
        """
        This is called on each inventory item in the shopping cart when the
        purchase goes through.
        """
        raise NotImplementedError

    def generate_receipt_instructions(self):
        """
        This is called on each item in a purchased order to generate receipt instructions.
        This should return a list of `ReceiptInstruction`s in HTML string
        Default implementation is to return an empty set
        """
        return self.pk_with_subclass, set([])

    @property
    def pk_with_subclass(self):
        """
        Returns a named tuple that annotates the pk of this instance with its class, to fully represent
        a pk of a subclass (inclusive) of OrderItem
        """
        return OrderItemSubclassPK(type(self), self.pk)

    @property
    def is_discounted(self):
        """
        Returns True if the item a discount coupon has been applied to the OrderItem and False otherwise.
        Earlier, the OrderItems were stored with an empty list_price if a discount had not been applied.
        Now we consider the item to be non discounted if list_price is None or list_price == unit_cost. In
        these lines, an item is discounted if it's non-None and list_price and unit_cost mismatch.
        This should work with both new and old records.
        """
        return self.list_price and self.list_price != self.unit_cost

    def get_list_price(self):
        """
        Returns the unit_cost if no discount has been applied, or the list_price if it is defined.
        """
        return self.list_price if self.list_price else self.unit_cost

    @property
    def single_item_receipt_template(self):
        """
        The template that should be used when there's only one item in the order
        """
        return 'shoppingcart/receipt.html'

    @property
    def single_item_receipt_context(self):
        """
        Extra variables needed to render the template specified in
        `single_item_receipt_template`
        """
        return {}

    def additional_instruction_text(self, **kwargs):  # pylint: disable=unused-argument
        """
        Individual instructions for this order item.

        Currently, only used for emails.
        """
        return ''

    @property
    def pdf_receipt_display_name(self):
        """
            How to display this item on a PDF printed receipt file.
            This can be overridden by the subclasses of OrderItem
        """
        course_key = getattr(self, 'course_id', None)
        if course_key:
            course = get_course_by_id(course_key, depth=0)
            return course.display_name
        else:
            raise Exception(
                "Not Implemented. OrderItems that are not Course specific should have"
                " a overridden pdf_receipt_display_name property"
            )

    def analytics_data(self):
        """Simple function used to construct analytics data for the OrderItem.

        The default implementation returns defaults for most attributes. When no name or
        category is specified by the implementation, the string 'N/A' is placed for the
        name and category.  This should be handled appropriately by all implementations.

        Returns
            A dictionary containing analytics data for this OrderItem.

        """
        return {
            'id': self.id,
            'sku': type(self).__name__,
            'name': 'N/A',
            'price': str(self.unit_cost),
            'quantity': self.qty,
            'category': 'N/A',
        }

    def retire(self):
        """
        Called by the `retire` method defined in the `Order` class. Retires
        an order item if its (and its order's) status was erroneously not
        updated to "purchased" after the order was processed.
        """
        self.status = ORDER_STATUS_MAP[self.status]
        self.save()


class Invoice(TimeStampedModel):
    """
    This table capture all the information needed to support "invoicing"
    which is when a user wants to purchase Registration Codes,
    but will not do so via a Credit Card transaction.
    """
    class Meta(object):
        app_label = "shoppingcart"

    company_name = models.CharField(max_length=255, db_index=True)
    company_contact_name = models.CharField(max_length=255)
    company_contact_email = models.CharField(max_length=255)
    recipient_name = models.CharField(max_length=255)
    recipient_email = models.CharField(max_length=255)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, null=True, blank=True)
    address_line_3 = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True)
    state = models.CharField(max_length=255, null=True)
    zip = models.CharField(max_length=15, null=True)
    country = models.CharField(max_length=64, null=True)

    # This field has been deprecated.
    # The total amount can now be calculated as the sum
    # of each invoice item associated with the invoice.
    # For backwards compatibility, this field is maintained
    # and written to during invoice creation.
    total_amount = models.FloatField()

    # This field has been deprecated in order to support
    # invoices for items that are not course-related.
    # Although this field is still maintained for backwards
    # compatibility, you should use CourseRegistrationCodeInvoiceItem
    # to look up the course ID for purchased redeem codes.
    course_id = CourseKeyField(max_length=255, db_index=True)

    internal_reference = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text=ugettext_lazy("Internal reference code for this invoice.")
    )
    customer_reference_number = models.CharField(
        max_length=63,
        null=True,
        blank=True,
        help_text=ugettext_lazy("Customer's reference code for this invoice.")
    )
    is_valid = models.BooleanField(default=True)

    @classmethod
    def get_invoice_total_amount_for_course(cls, course_key):
        """
        returns the invoice total amount generated by course.
        """
        result = cls.objects.filter(course_id=course_key, is_valid=True).aggregate(total=Sum('total_amount'))

        total = result.get('total', 0)
        return total if total else 0

    def generate_pdf_invoice(self, course, course_price, quantity, sale_price):
        """
        Generates the pdf invoice for the given course
        and returns the pdf_buffer.
        """
        discount_per_item = float(course_price) - sale_price / quantity
        list_price = course_price - discount_per_item
        items_data = [{
            'item_description': course.display_name,
            'quantity': quantity,
            'list_price': list_price,
            'discount': discount_per_item,
            'item_total': quantity * list_price
        }]
        pdf_buffer = BytesIO()
        PDFInvoice(
            items_data=items_data,
            item_id=str(self.id),
            date=datetime.now(pytz.utc),
            is_invoice=True,
            total_cost=float(self.total_amount),
            payment_received=0,
            balance=float(self.total_amount)
        ).generate_pdf(pdf_buffer)

        return pdf_buffer

    def snapshot(self):
        """Create a snapshot of the invoice.

        A snapshot is a JSON-serializable representation
        of the invoice's state, including its line items
        and associated transactions (payments/refunds).

        This is useful for saving the history of changes
        to the invoice.

        Returns:
            dict

        """
        return {
            'internal_reference': self.internal_reference,
            'customer_reference': self.customer_reference_number,
            'is_valid': self.is_valid,
            'contact_info': {
                'company_name': self.company_name,
                'company_contact_name': self.company_contact_name,
                'company_contact_email': self.company_contact_email,
                'recipient_name': self.recipient_name,
                'recipient_email': self.recipient_email,
                'address_line_1': self.address_line_1,
                'address_line_2': self.address_line_2,
                'address_line_3': self.address_line_3,
                'city': self.city,
                'state': self.state,
                'zip': self.zip,
                'country': self.country,
            },
            'items': [
                item.snapshot()
                for item in InvoiceItem.objects.filter(invoice=self).select_subclasses()
            ],
            'transactions': [
                trans.snapshot()
                for trans in InvoiceTransaction.objects.filter(invoice=self)
            ],
        }

    def __unicode__(self):
        label = (
            unicode(self.internal_reference)
            if self.internal_reference
            else u"No label"
        )

        created = (
            self.created.strftime("%Y-%m-%d")
            if self.created
            else u"No date"
        )

        return u"{label} ({date_created})".format(
            label=label, date_created=created
        )


INVOICE_TRANSACTION_STATUSES = (
    # A payment/refund is in process, but money has not yet been transferred
    ('started', 'started'),

    # A payment/refund has completed successfully
    # This should be set ONLY once money has been successfully exchanged.
    ('completed', 'completed'),

    # A payment/refund was promised, but was cancelled before
    # money had been transferred.  An example would be
    # cancelling a refund check before the recipient has
    # a chance to deposit it.
    ('cancelled', 'cancelled')
)


class InvoiceTransaction(TimeStampedModel):
    """Record payment and refund information for invoices.

    There are two expected use cases:

    1) We send an invoice to someone, and they send us a check.
       We then manually create an invoice transaction to represent
       the payment.

    2) We send an invoice to someone, and they pay us.  Later, we
       need to issue a refund for the payment.  We manually
       create a transaction with a negative amount to represent
       the refund.

    """
    class Meta(object):
        app_label = "shoppingcart"

    invoice = models.ForeignKey(Invoice)
    amount = models.DecimalField(
        default=0.0, decimal_places=2, max_digits=30,
        help_text=ugettext_lazy(
            "The amount of the transaction.  Use positive amounts for payments"
            " and negative amounts for refunds."
        )
    )
    currency = models.CharField(
        default="usd",
        max_length=8,
        help_text=ugettext_lazy("Lower-case ISO currency codes")
    )
    comments = models.TextField(
        null=True,
        blank=True,
        help_text=ugettext_lazy("Optional: provide additional information for this transaction")
    )
    status = models.CharField(
        max_length=32,
        default='started',
        choices=INVOICE_TRANSACTION_STATUSES,
        help_text=ugettext_lazy(
            "The status of the payment or refund. "
            "'started' means that payment is expected, but money has not yet been transferred. "
            "'completed' means that the payment or refund was received. "
            "'cancelled' means that payment or refund was expected, but was cancelled before money was transferred. "
        )
    )
    created_by = models.ForeignKey(User)
    last_modified_by = models.ForeignKey(User, related_name='last_modified_by_user')

    @classmethod
    def get_invoice_transaction(cls, invoice_id):
        """
        if found Returns the Invoice Transaction object for the given invoice_id
        else returns None
        """
        try:
            return cls.objects.get(Q(invoice_id=invoice_id), Q(status='completed') | Q(status='refunded'))
        except InvoiceTransaction.DoesNotExist:
            return None

    @classmethod
    def get_total_amount_of_paid_course_invoices(cls, course_key):
        """
        returns the total amount of the paid invoices.
        """
        result = cls.objects.filter(amount__gt=0, invoice__course_id=course_key, status='completed').aggregate(
            total=Sum(
                'amount',
                output_field=models.DecimalField(decimal_places=2, max_digits=30)
            )
        )

        total = result.get('total', 0)
        return total if total else 0

    def snapshot(self):
        """Create a snapshot of the invoice transaction.

        The returned dictionary is JSON-serializable.

        Returns:
            dict

        """
        return {
            'amount': unicode(self.amount),
            'currency': self.currency,
            'comments': self.comments,
            'status': self.status,
            'created_by': self.created_by.username,
            'last_modified_by': self.last_modified_by.username
        }


class InvoiceItem(TimeStampedModel):
    """
    This is the basic interface for invoice items.

    Each invoice item represents a "line" in the invoice.
    For example, in an invoice for course registration codes,
    there might be an invoice item representing 10 registration
    codes for the DemoX course.

    """
    class Meta(object):
        app_label = "shoppingcart"

    objects = InheritanceManager()
    invoice = models.ForeignKey(Invoice, db_index=True)
    qty = models.IntegerField(
        default=1,
        help_text=ugettext_lazy("The number of items sold.")
    )
    unit_price = models.DecimalField(
        default=0.0,
        decimal_places=2,
        max_digits=30,
        help_text=ugettext_lazy("The price per item sold, including discounts.")
    )
    currency = models.CharField(
        default="usd",
        max_length=8,
        help_text=ugettext_lazy("Lower-case ISO currency codes")
    )

    def snapshot(self):
        """Create a snapshot of the invoice item.

        The returned dictionary is JSON-serializable.

        Returns:
            dict

        """
        return {
            'qty': self.qty,
            'unit_price': unicode(self.unit_price),
            'currency': self.currency
        }


class CourseRegistrationCodeInvoiceItem(InvoiceItem):
    """
    This is an invoice item that represents a payment for
    a course registration.

    """
    class Meta(object):
        app_label = "shoppingcart"

    course_id = CourseKeyField(max_length=128, db_index=True)

    def snapshot(self):
        """Create a snapshot of the invoice item.

        This is the same as a snapshot for other invoice items,
        with the addition of a `course_id` field.

        Returns:
            dict

        """
        snapshot = super(CourseRegistrationCodeInvoiceItem, self).snapshot()
        snapshot['course_id'] = unicode(self.course_id)
        return snapshot


class InvoiceHistory(models.Model):
    """History of changes to invoices.

    This table stores snapshots of invoice state,
    including the associated line items and transactions
    (payments/refunds).

    Entries in the table are created, but never deleted
    or modified.

    We use Django signals to save history entries on change
    events.  These signals are fired within a database
    transaction, so the history record is created only
    if the invoice change is successfully persisted.

    """
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    invoice = models.ForeignKey(Invoice)

    # JSON-serialized representation of the current state
    # of the invoice, including its line items and
    # transactions (payments/refunds).
    snapshot = models.TextField(blank=True)

    @classmethod
    def save_invoice_snapshot(cls, invoice):
        """Save a snapshot of the invoice's current state.

        Arguments:
            invoice (Invoice): The invoice to save.

        """
        cls.objects.create(
            invoice=invoice,
            snapshot=json.dumps(invoice.snapshot())
        )

    @staticmethod
    def snapshot_receiver(sender, instance, **kwargs):  # pylint: disable=unused-argument
        """Signal receiver that saves a snapshot of an invoice.

        Arguments:
            sender: Not used, but required by Django signals.
            instance (Invoice, InvoiceItem, or InvoiceTransaction)

        """
        if isinstance(instance, Invoice):
            InvoiceHistory.save_invoice_snapshot(instance)
        elif hasattr(instance, 'invoice'):
            InvoiceHistory.save_invoice_snapshot(instance.invoice)

    class Meta(object):
        get_latest_by = "timestamp"
        app_label = "shoppingcart"


# Hook up Django signals to record changes in the history table.
# We record any change to an invoice, invoice item, or transaction.
# We also record any deletion of a transaction, since users can delete
# transactions via Django admin.
# Note that we need to include *each* InvoiceItem subclass
# here, since Django signals do not fire automatically for subclasses
# of the "sender" class.
post_save.connect(InvoiceHistory.snapshot_receiver, sender=Invoice)
post_save.connect(InvoiceHistory.snapshot_receiver, sender=InvoiceItem)
post_save.connect(InvoiceHistory.snapshot_receiver, sender=CourseRegistrationCodeInvoiceItem)
post_save.connect(InvoiceHistory.snapshot_receiver, sender=InvoiceTransaction)
post_delete.connect(InvoiceHistory.snapshot_receiver, sender=InvoiceTransaction)


class CourseRegistrationCode(models.Model):
    """
    This table contains registration codes
    With registration code, a user can register for a course for free
    """
    class Meta(object):
        app_label = "shoppingcart"

    code = models.CharField(max_length=32, db_index=True, unique=True)
    course_id = CourseKeyField(max_length=255, db_index=True)
    created_by = models.ForeignKey(User, related_name='created_by_user')
    created_at = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, db_index=True, null=True, related_name="purchase_order")
    mode_slug = models.CharField(max_length=100, null=True)
    is_valid = models.BooleanField(default=True)

    # For backwards compatibility, we maintain the FK to "invoice"
    # In the future, we will remove this in favor of the FK
    # to "invoice_item" (which can be used to look up the invoice).
    invoice = models.ForeignKey(Invoice, null=True)
    invoice_item = models.ForeignKey(CourseRegistrationCodeInvoiceItem, null=True)

    @classmethod
    def order_generated_registration_codes(cls, course_id):
        """
        Returns the registration codes that were generated
        via bulk purchase scenario.
        """
        return cls.objects.filter(order__isnull=False, course_id=course_id)

    @classmethod
    def invoice_generated_registration_codes(cls, course_id):
        """
        Returns the registration codes that were generated
        via invoice.
        """
        return cls.objects.filter(invoice__isnull=False, course_id=course_id)


class RegistrationCodeRedemption(models.Model):
    """
    This model contains the registration-code redemption info
    """
    class Meta(object):
        app_label = "shoppingcart"

    order = models.ForeignKey(Order, db_index=True, null=True)
    registration_code = models.ForeignKey(CourseRegistrationCode, db_index=True)
    redeemed_by = models.ForeignKey(User, db_index=True)
    redeemed_at = models.DateTimeField(auto_now_add=True, null=True)
    course_enrollment = models.ForeignKey(CourseEnrollment, null=True)

    @classmethod
    def registration_code_used_for_enrollment(cls, course_enrollment):
        """
        Returns RegistrationCodeRedemption object if registration code
        has been used during the course enrollment else Returns None.
        """
        # theoretically there could be more than one (e.g. someone self-unenrolls
        # then re-enrolls with a different regcode)
        reg_codes = cls.objects.filter(course_enrollment=course_enrollment).order_by('-redeemed_at')
        if reg_codes:
            # return the first one. In all normal use cases of registration codes
            # the user will only have one
            return reg_codes[0]

        return None

    @classmethod
    def is_registration_code_redeemed(cls, course_reg_code):
        """
        Checks the existence of the registration code
        in the RegistrationCodeRedemption
        """
        return cls.objects.filter(registration_code__code=course_reg_code).exists()

    @classmethod
    def get_registration_code_redemption(cls, code, course_id):
        """
        Returns the registration code redemption object if found else returns None.
        """
        try:
            code_redemption = cls.objects.get(registration_code__code=code, registration_code__course_id=course_id)
        except cls.DoesNotExist:
            code_redemption = None
        return code_redemption

    @classmethod
    def create_invoice_generated_registration_redemption(cls, course_reg_code, user):  # pylint: disable=invalid-name
        """
        This function creates a RegistrationCodeRedemption entry in case the registration codes were invoice generated
        and thus the order_id is missing.
        """
        code_redemption = RegistrationCodeRedemption(registration_code=course_reg_code, redeemed_by=user)
        code_redemption.save()
        return code_redemption


class SoftDeleteCouponManager(models.Manager):
    """ Use this manager to get objects that have a is_active=True """
    def get_active_coupons_queryset(self):
        """
        filter the is_active = True Coupons only
        """
        return super(SoftDeleteCouponManager, self).get_queryset().filter(is_active=True)

    def get_queryset(self):
        """
        get all the coupon objects
        """
        return super(SoftDeleteCouponManager, self).get_queryset()


class Coupon(models.Model):
    """
    This table contains coupon codes
    A user can get a discount offer on course if provide coupon code
    """
    class Meta(object):
        app_label = "shoppingcart"

    code = models.CharField(max_length=32, db_index=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    course_id = CourseKeyField(max_length=255)
    percentage_discount = models.IntegerField(default=0)
    created_by = models.ForeignKey(User)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    expiration_date = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return "[Coupon] code: {} course: {}".format(self.code, self.course_id)

    objects = SoftDeleteCouponManager()

    @property
    def display_expiry_date(self):
        """
        return the coupon expiration date in the readable format
        """
        return (self.expiration_date - timedelta(days=1)).strftime("%B %d, %Y") if self.expiration_date else None


class CouponRedemption(models.Model):
    """
    This table contain coupon redemption info
    """
    class Meta(object):
        app_label = "shoppingcart"

    order = models.ForeignKey(Order, db_index=True)
    user = models.ForeignKey(User, db_index=True)
    coupon = models.ForeignKey(Coupon, db_index=True)

    @classmethod
    def remove_code_redemption_from_item(cls, item, user):
        """
        If an item removed from shopping cart then we will remove
        the corresponding redemption info of coupon code
        """
        order_item_course_id = item.course_id
        try:
            # Try to remove redemption information of coupon code, If exist.
            coupon_redemption = cls.objects.get(
                user=user,
                coupon__course_id=order_item_course_id if order_item_course_id else CourseKeyField.Empty,
                order=item.order_id
            )
            coupon_redemption.delete()
            log.info(
                u'Coupon "%s" redemption entry removed for user "%s" for order item "%s"',
                coupon_redemption.coupon.code,
                user,
                str(item.id),
            )
        except CouponRedemption.DoesNotExist:
            log.debug(u'Code redemption does not exist for order item id=%s.', str(item.id))

    @classmethod
    def remove_coupon_redemption_from_cart(cls, user, cart):
        """
        This method delete coupon redemption
        """
        coupon_redemption = cls.objects.filter(user=user, order=cart)
        if coupon_redemption:
            coupon_redemption.delete()
            log.info(u'Coupon redemption entry removed for user %s for order %s', user, cart.id)

    @classmethod
    def get_discount_price(cls, percentage_discount, value):
        """
        return discounted price against coupon
        """
        discount = Decimal("{0:.2f}".format(Decimal(percentage_discount / 100.00) * value))
        return value - discount

    @classmethod
    def add_coupon_redemption(cls, coupon, order, cart_items):
        """
        add coupon info into coupon_redemption model
        """
        is_redemption_applied = False
        coupon_redemptions = cls.objects.filter(order=order, user=order.user)
        for coupon_redemption in coupon_redemptions:
            if coupon_redemption.coupon.code != coupon.code or coupon_redemption.coupon.id == coupon.id:
                log.exception(
                    u"Coupon redemption already exist for user '%s' against order id '%s'",
                    order.user.username,
                    order.id,
                )
                raise MultipleCouponsNotAllowedException

        for item in cart_items:
            if item.course_id:
                if item.course_id == coupon.course_id:
                    coupon_redemption = cls(order=order, user=order.user, coupon=coupon)
                    coupon_redemption.save()
                    discount_price = cls.get_discount_price(coupon.percentage_discount, item.unit_cost)
                    item.list_price = item.unit_cost
                    item.unit_cost = discount_price
                    item.save()
                    log.info(
                        u"Discount generated for user %s against order id '%s'",
                        order.user.username,
                        order.id,
                    )
                    is_redemption_applied = True
                    return is_redemption_applied

        return is_redemption_applied

    @classmethod
    def get_top_discount_codes_used(cls, course_id):
        """
        Returns the top discount codes used.

        QuerySet = [
            {
                'coupon__percentage_discount': 22,
                'coupon__code': '12',
                'coupon__used_count': '2',
            },
            {
                ...
            }
        ]
        """
        return cls.objects.filter(order__status='purchased', coupon__course_id=course_id).values(
            'coupon__code', 'coupon__percentage_discount'
        ).annotate(coupon__used_count=Count('coupon__code')).order_by('-coupon__used_count')

    @classmethod
    def get_total_coupon_code_purchases(cls, course_id):
        """
        returns total seats purchases using coupon codes
        """
        return cls.objects.filter(order__status='purchased', coupon__course_id=course_id).aggregate(Count('coupon'))


class PaidCourseRegistration(OrderItem):
    """
    This is an inventory item for paying for a course registration
    """
    class Meta(object):
        app_label = "shoppingcart"

    course_id = CourseKeyField(max_length=128, db_index=True)
    mode = models.SlugField(default=CourseMode.DEFAULT_MODE_SLUG)
    course_enrollment = models.ForeignKey(CourseEnrollment, null=True)

    @classmethod
    def get_self_purchased_seat_count(cls, course_key, status='purchased'):
        """
        returns the count of paid_course items filter by course_id and status.
        """
        return cls.objects.filter(course_id=course_key, status=status).count()

    @classmethod
    def get_course_item_for_user_enrollment(cls, user, course_id, course_enrollment):
        """
        Returns PaidCourseRegistration object if user has payed for
        the course enrollment else Returns None
        """
        try:
            return cls.objects.filter(course_id=course_id, user=user, course_enrollment=course_enrollment,
                                      status='purchased').latest('id')
        except PaidCourseRegistration.DoesNotExist:
            return None

    @classmethod
    def contained_in_order(cls, order, course_id):
        """
        Is the course defined by course_id contained in the order?
        """
        return course_id in [
            item.course_id
            for item in order.orderitem_set.all().select_subclasses("paidcourseregistration")
            if isinstance(item, cls)
        ]

    @classmethod
    def get_total_amount_of_purchased_item(cls, course_key, status='purchased'):
        """
        This will return the total amount of money that a purchased course generated
        """
        total_cost = 0
        result = cls.objects.filter(course_id=course_key, status=status).aggregate(
            total=Sum(
                F('qty') * F('unit_cost'),
                output_field=models.DecimalField(decimal_places=2, max_digits=30)
            )
        )

        if result['total'] is not None:
            total_cost = result['total']

        return total_cost

    @classmethod
    @transaction.atomic
    def add_to_order(cls, order, course_id, mode_slug=CourseMode.DEFAULT_MODE_SLUG, cost=None, currency=None):
        """
        A standardized way to create these objects, with sensible defaults filled in.
        Will update the cost if called on an order that already carries the course.

        Returns the order item
        """
        # First a bunch of sanity checks:
        # actually fetch the course to make sure it exists, use this to
        # throw errors if it doesn't.
        course = modulestore().get_course(course_id)
        if not course:
            log.error("User {} tried to add non-existent course {} to cart id {}"
                      .format(order.user.email, course_id, order.id))
            raise CourseDoesNotExistException

        if cls.contained_in_order(order, course_id):
            log.warning(
                u"User %s tried to add PaidCourseRegistration for course %s, already in cart id %s",
                order.user.email,
                course_id,
                order.id,
            )
            raise ItemAlreadyInCartException

        if CourseEnrollment.is_enrolled(user=order.user, course_key=course_id):
            log.warning("User {} trying to add course {} to cart id {}, already registered"
                        .format(order.user.email, course_id, order.id))
            raise AlreadyEnrolledInCourseException

        ### Validations done, now proceed
        ### handle default arguments for mode_slug, cost, currency
        course_mode = CourseMode.mode_for_course(course_id, mode_slug)
        if not course_mode:
            # user could have specified a mode that's not set, in that case return the DEFAULT_MODE
            course_mode = CourseMode.DEFAULT_MODE
        if not cost:
            cost = course_mode.min_price
        if not currency:
            currency = course_mode.currency

        super(PaidCourseRegistration, cls).add_to_order(order, course_id, cost, currency=currency)

        item, created = cls.objects.get_or_create(order=order, user=order.user, course_id=course_id)
        item.status = order.status
        item.mode = course_mode.slug
        item.qty = 1
        item.unit_cost = cost
        item.list_price = cost
        item.line_desc = _(u'Registration for Course: {course_name}').format(
            course_name=course.display_name_with_default)
        item.currency = currency
        order.currency = currency
        item.report_comments = item.csv_report_comments
        order.save()
        item.save()
        log.info("User {} added course registration {} to cart: order {}"
                 .format(order.user.email, course_id, order.id))
        return item

    def purchased_callback(self):
        """
        When purchased, this should enroll the user in the course.  We are assuming that
        course settings for enrollment date are configured such that only if the (user.email, course_id) pair is found
        in CourseEnrollmentAllowed will the user be allowed to enroll.  Otherwise requiring payment
        would in fact be quite silly since there's a clear back door.
        """
        if not modulestore().has_course(self.course_id):
            msg = u"The customer purchased Course {0}, but that course doesn't exist!".format(self.course_id)
            log.error(msg)
            raise PurchasedCallbackException(msg)

        # enroll in course and link to the enrollment_id
        self.course_enrollment = CourseEnrollment.enroll(user=self.user, course_key=self.course_id, mode=self.mode)
        self.save()

        log.info("Enrolled {0} in paid course {1}, paid ${2}"
                 .format(self.user.email, self.course_id, self.line_cost))

    def generate_receipt_instructions(self):
        """
        Generates instructions when the user has purchased a PaidCourseRegistration.
        Basically tells the user to visit the dashboard to see their new classes
        """
        notification = _(
            u"Please visit your {link_start}dashboard{link_end} "
            u"to see your new course."
        ).format(
            link_start=u'<a href="{url}">'.format(url=reverse('dashboard')),
            link_end=u'</a>',
        )

        return self.pk_with_subclass, set([notification])

    @property
    def csv_report_comments(self):
        """
        Tries to fetch an annotation associated with the course_id from the database.  If not found, returns u"".
        Otherwise returns the annotation
        """
        try:
            return PaidCourseRegistrationAnnotation.objects.get(course_id=self.course_id).annotation
        except PaidCourseRegistrationAnnotation.DoesNotExist:
            return u""

    def analytics_data(self):
        """Simple function used to construct analytics data for the OrderItem.

        If the Order Item is associated with a course, additional fields will be populated with
        course information. If there is a mode associated, the mode data is included in the SKU.

        Returns
            A dictionary containing analytics data for this OrderItem.

        """
        data = super(PaidCourseRegistration, self).analytics_data()
        sku = data['sku']
        if self.course_id != CourseKeyField.Empty:
            data['name'] = unicode(self.course_id)
            data['category'] = unicode(self.course_id.org)
        if self.mode:
            data['sku'] = sku + u'.' + unicode(self.mode)
        return data


class CourseRegCodeItem(OrderItem):
    """
    This is an inventory item for paying for
    generating course registration codes
    """
    class Meta(object):
        app_label = "shoppingcart"

    course_id = CourseKeyField(max_length=128, db_index=True)
    mode = models.SlugField(default=CourseMode.DEFAULT_MODE_SLUG)

    @classmethod
    def get_bulk_purchased_seat_count(cls, course_key, status='purchased'):
        """
        returns the sum of bulk purchases seats.
        """
        total = 0
        result = cls.objects.filter(course_id=course_key, status=status).aggregate(total=Sum('qty'))

        if result['total'] is not None:
            total = result['total']

        return total

    @classmethod
    def contained_in_order(cls, order, course_id):
        """
        Is the course defined by course_id contained in the order?
        """
        return course_id in [
            item.course_id
            for item in order.orderitem_set.all().select_subclasses("courseregcodeitem")
            if isinstance(item, cls)
        ]

    @classmethod
    def get_total_amount_of_purchased_item(cls, course_key, status='purchased'):
        """
        This will return the total amount of money that a purchased course generated
        """
        total_cost = 0
        result = cls.objects.filter(course_id=course_key, status=status).aggregate(
            total=Sum(
                F('qty') * F('unit_cost'),
                output_field=models.DecimalField(decimal_places=2, max_digits=30)
            )
        )

        if result['total'] is not None:
            total_cost = result['total']

        return total_cost

    @classmethod
    @transaction.atomic
    def add_to_order(cls, order, course_id, qty, mode_slug=CourseMode.DEFAULT_MODE_SLUG, cost=None, currency=None):  # pylint: disable=arguments-differ
        """
        A standardized way to create these objects, with sensible defaults filled in.
        Will update the cost if called on an order that already carries the course.

        Returns the order item
        """
        # First a bunch of sanity checks:
        # actually fetch the course to make sure it exists, use this to
        # throw errors if it doesn't.
        course = modulestore().get_course(course_id)
        if not course:
            log.error("User {} tried to add non-existent course {} to cart id {}"
                      .format(order.user.email, course_id, order.id))
            raise CourseDoesNotExistException

        if cls.contained_in_order(order, course_id):
            log.warning("User {} tried to add PaidCourseRegistration for course {}, already in cart id {}"
                        .format(order.user.email, course_id, order.id))
            raise ItemAlreadyInCartException

        if CourseEnrollment.is_enrolled(user=order.user, course_key=course_id):
            log.warning("User {} trying to add course {} to cart id {}, already registered"
                        .format(order.user.email, course_id, order.id))
            raise AlreadyEnrolledInCourseException

        ### Validations done, now proceed
        ### handle default arguments for mode_slug, cost, currency
        course_mode = CourseMode.mode_for_course(course_id, mode_slug)
        if not course_mode:
            # user could have specified a mode that's not set, in that case return the DEFAULT_MODE
            course_mode = CourseMode.DEFAULT_MODE
        if not cost:
            cost = course_mode.min_price
        if not currency:
            currency = course_mode.currency

        super(CourseRegCodeItem, cls).add_to_order(order, course_id, cost, currency=currency)

        item, created = cls.objects.get_or_create(order=order, user=order.user, course_id=course_id)  # pylint: disable=unused-variable
        item.status = order.status
        item.mode = course_mode.slug
        item.unit_cost = cost
        item.list_price = cost
        item.qty = qty
        item.line_desc = _(u'Enrollment codes for Course: {course_name}').format(
            course_name=course.display_name_with_default)
        item.currency = currency
        order.currency = currency
        item.report_comments = item.csv_report_comments
        order.save()
        item.save()
        log.info("User {} added course registration {} to cart: order {}"
                 .format(order.user.email, course_id, order.id))
        return item

    def purchased_callback(self):
        """
        The purchase is completed, this OrderItem type will generate Registration Codes that will
        be redeemed by users
        """
        if not modulestore().has_course(self.course_id):
            msg = u"The customer purchased Course {0}, but that course doesn't exist!".format(self.course_id)
            log.error(msg)
            raise PurchasedCallbackException(msg)
        total_registration_codes = int(self.qty)

        # we need to import here because of a circular dependency
        # we should ultimately refactor code to have save_registration_code in this models.py
        # file, but there's also a shared dependency on a random string generator which
        # is in another PR (for another feature)
        from instructor.views.api import save_registration_code
        for i in range(total_registration_codes):  # pylint: disable=unused-variable
            save_registration_code(self.user, self.course_id, self.mode, order=self.order)

        log.info("Enrolled {0} in paid course {1}, paid ${2}"
                 .format(self.user.email, self.course_id, self.line_cost))

    @property
    def csv_report_comments(self):
        """
        Tries to fetch an annotation associated with the course_id from the database.  If not found, returns u"".
        Otherwise returns the annotation
        """
        try:
            return CourseRegCodeItemAnnotation.objects.get(course_id=self.course_id).annotation
        except CourseRegCodeItemAnnotation.DoesNotExist:
            return u""

    def analytics_data(self):
        """Simple function used to construct analytics data for the OrderItem.

        If the OrderItem is associated with a course, additional fields will be populated with
        course information. If a mode is available, it will be included in the SKU.

        Returns
            A dictionary containing analytics data for this OrderItem.

        """
        data = super(CourseRegCodeItem, self).analytics_data()
        sku = data['sku']
        if self.course_id != CourseKeyField.Empty:
            data['name'] = unicode(self.course_id)
            data['category'] = unicode(self.course_id.org)
        if self.mode:
            data['sku'] = sku + u'.' + unicode(self.mode)
        return data


class CourseRegCodeItemAnnotation(models.Model):
    """
    A model that maps course_id to an additional annotation.  This is specifically needed because when Stanford
    generates report for the paid courses, each report item must contain the payment account associated with a course.
    And unfortunately we didn't have the concept of a "SKU" or stock item where we could keep this association,
    so this is to retrofit it.
    """
    class Meta(object):
        app_label = "shoppingcart"

    course_id = CourseKeyField(unique=True, max_length=128, db_index=True)
    annotation = models.TextField(null=True)

    def __unicode__(self):
        # pylint: disable=no-member
        return u"{} : {}".format(self.course_id.to_deprecated_string(), self.annotation)


class PaidCourseRegistrationAnnotation(models.Model):
    """
    A model that maps course_id to an additional annotation.  This is specifically needed because when Stanford
    generates report for the paid courses, each report item must contain the payment account associated with a course.
    And unfortunately we didn't have the concept of a "SKU" or stock item where we could keep this association,
    so this is to retrofit it.
    """
    class Meta(object):
        app_label = "shoppingcart"

    course_id = CourseKeyField(unique=True, max_length=128, db_index=True)
    annotation = models.TextField(null=True)

    def __unicode__(self):
        # pylint: disable=no-member
        return u"{} : {}".format(self.course_id.to_deprecated_string(), self.annotation)


class CertificateItem(OrderItem):
    """
    This is an inventory item for purchasing certificates
    """
    class Meta(object):
        app_label = "shoppingcart"

    course_id = CourseKeyField(max_length=128, db_index=True)
    course_enrollment = models.ForeignKey(CourseEnrollment)
    mode = models.SlugField()

    @receiver(UNENROLL_DONE)
    def refund_cert_callback(sender, course_enrollment=None, skip_refund=False, **kwargs):  # pylint: disable=no-self-argument,unused-argument
        """
        When a CourseEnrollment object calls its unenroll method, this function checks to see if that unenrollment
        occurred in a verified certificate that was within the refund deadline.  If so, it actually performs the
        refund.

        Returns the refunded certificate on a successful refund; else, it returns nothing.
        """

        # Only refund verified cert unenrollments that are within bounds of the expiration date
        if (not course_enrollment.refundable()) or skip_refund:
            return

        target_certs = CertificateItem.objects.filter(course_id=course_enrollment.course_id, user_id=course_enrollment.user, status='purchased', mode='verified')
        try:
            target_cert = target_certs[0]
        except IndexError:
            log.error(
                u"Matching CertificateItem not found while trying to refund. User %s, Course %s",
                course_enrollment.user,
                course_enrollment.course_id,
            )
            return
        target_cert.status = 'refunded'
        target_cert.refund_requested_time = datetime.now(pytz.utc)
        target_cert.save()

        target_cert.order.refund()

        order_number = target_cert.order_id
        # send billing an email so they can handle refunding
        subject = _("[Refund] User-Requested Refund")
        message = "User {user} ({user_email}) has requested a refund on Order #{order_number}.".format(user=course_enrollment.user,
                                                                                                       user_email=course_enrollment.user.email,
                                                                                                       order_number=order_number)
        to_email = [settings.PAYMENT_SUPPORT_EMAIL]
        from_email = microsite.get_value('payment_support_email', settings.PAYMENT_CONFIRM_EMAIL)
        try:
            send_mail(subject, message, from_email, to_email, fail_silently=False)
        except Exception as exception:  # pylint: disable=broad-except
            err_str = ('Failed sending email to billing to request a refund for verified certificate'
                       ' (User {user}, Course {course}, CourseEnrollmentID {ce_id}, Order #{order})\n{exception}')
            log.error(err_str.format(
                user=course_enrollment.user,
                course=course_enrollment.course_id,
                ce_id=course_enrollment.id,
                order=order_number,
                exception=exception,
            ))

        return target_cert

    @classmethod
    @transaction.atomic
    def add_to_order(cls, order, course_id, cost, mode, currency='usd'):
        """
        Add a CertificateItem to an order

        Returns the CertificateItem object after saving

        `order` - an order that this item should be added to, generally the cart order
        `course_id` - the course that we would like to purchase as a CertificateItem
        `cost` - the amount the user will be paying for this CertificateItem
        `mode` - the course mode that this certificate is going to be issued for

        This item also creates a new enrollment if none exists for this user and this course.

        Example Usage:
            cart = Order.get_cart_for_user(user)
            CertificateItem.add_to_order(cart, 'edX/Test101/2013_Fall', 30, 'verified')

        """
        super(CertificateItem, cls).add_to_order(order, course_id, cost, currency=currency)

        course_enrollment = CourseEnrollment.get_or_create_enrollment(order.user, course_id)

        # do some validation on the enrollment mode
        valid_modes = CourseMode.modes_for_course_dict(course_id)
        if mode in valid_modes:
            mode_info = valid_modes[mode]
        else:
            msg = u"Mode {mode} does not exist for {course_id}".format(mode=mode, course_id=course_id)
            log.error(msg)
            raise InvalidCartItem(
                _(u"Mode {mode} does not exist for {course_id}").format(mode=mode, course_id=course_id)
            )

        item, _created = cls.objects.get_or_create(
            order=order,
            user=order.user,
            course_id=course_id,
            course_enrollment=course_enrollment,
            mode=mode,
        )
        item.status = order.status
        item.qty = 1
        item.unit_cost = cost
        item.list_price = cost
        course_name = modulestore().get_course(course_id).display_name
        # Translators: In this particular case, mode_name refers to a
        # particular mode (i.e. Honor Code Certificate, Verified Certificate, etc)
        # by which a user could enroll in the given course.
        item.line_desc = _("{mode_name} for course {course}").format(
            mode_name=mode_info.name,
            course=course_name
        )
        item.currency = currency
        order.currency = currency
        order.save()
        item.save()
        return item

    def purchased_callback(self):
        """
        When purchase goes through, activate and update the course enrollment for the correct mode
        """
        self.course_enrollment.change_mode(self.mode)
        self.course_enrollment.activate()

    def additional_instruction_text(self):
        verification_reminder = ""
        is_enrollment_mode_verified = self.course_enrollment.is_verified_enrollment()

        if is_enrollment_mode_verified:
            domain = microsite.get_value('SITE_NAME', settings.SITE_NAME)
            path = reverse('verify_student_verify_now', kwargs={'course_id': unicode(self.course_id)})
            verification_url = "http://{domain}{path}".format(domain=domain, path=path)

            verification_reminder = _(
                "If you haven't verified your identity yet, please start the verification process ({verification_url})."
            ).format(verification_url=verification_url)

        refund_reminder = _(
            "You have up to two weeks into the course to unenroll and receive a full refund."
            "To receive your refund, contact {billing_email}. "
            "Please include your order number in your email. "
            "Please do NOT include your credit card information."
        ).format(
            billing_email=settings.PAYMENT_SUPPORT_EMAIL
        )

        # Need this to be unicode in case the reminder strings
        # have been translated and contain non-ASCII unicode
        return u"{verification_reminder} {refund_reminder}".format(
            verification_reminder=verification_reminder,
            refund_reminder=refund_reminder
        )

    @classmethod
    def verified_certificates_count(cls, course_id, status):
        """Return a queryset of CertificateItem for every verified enrollment in course_id with the given status."""
        return use_read_replica_if_available(
            CertificateItem.objects.filter(course_id=course_id, mode='verified', status=status).count())

    # TODO combine these three methods into one
    @classmethod
    def verified_certificates_monetary_field_sum(cls, course_id, status, field_to_aggregate):
        """
        Returns a Decimal indicating the total sum of field_to_aggregate for all verified certificates with a particular status.

        Sample usages:
        - status 'refunded' and field_to_aggregate 'unit_cost' will give the total amount of money refunded for course_id
        - status 'purchased' and field_to_aggregate 'service_fees' gives the sum of all service fees for purchased certificates
        etc
        """
        query = use_read_replica_if_available(
            CertificateItem.objects.filter(course_id=course_id, mode='verified', status=status)).aggregate(Sum(field_to_aggregate))[field_to_aggregate + '__sum']
        if query is None:
            return Decimal(0.00)
        else:
            return query

    @classmethod
    def verified_certificates_contributing_more_than_minimum(cls, course_id):
        return use_read_replica_if_available(
            CertificateItem.objects.filter(
                course_id=course_id,
                mode='verified',
                status='purchased',
                unit_cost__gt=(CourseMode.min_course_price_for_verified_for_currency(course_id, 'usd')))).count()

    def analytics_data(self):
        """Simple function used to construct analytics data for the OrderItem.

        If the CertificateItem is associated with a course, additional fields will be populated with
        course information. If there is a mode associated with the certificate, it is included in the SKU.

        Returns
            A dictionary containing analytics data for this OrderItem.

        """
        data = super(CertificateItem, self).analytics_data()
        sku = data['sku']
        if self.course_id != CourseKeyField.Empty:
            data['name'] = unicode(self.course_id)
            data['category'] = unicode(self.course_id.org)
        if self.mode:
            data['sku'] = sku + u'.' + unicode(self.mode)
        return data


class DonationConfiguration(ConfigurationModel):
    """Configure whether donations are enabled on the site."""
    class Meta(ConfigurationModel.Meta):
        app_label = "shoppingcart"


class Donation(OrderItem):
    """A donation made by a user.

    Donations can be made for a specific course or to the organization as a whole.
    Users can choose the donation amount.
    """

    class Meta(object):
        app_label = "shoppingcart"

    # Types of donations
    DONATION_TYPES = (
        ("general", "A general donation"),
        ("course", "A donation to a particular course")
    )

    # The type of donation
    donation_type = models.CharField(max_length=32, default="general", choices=DONATION_TYPES)

    # If a donation is made for a specific course, then store the course ID here.
    # If the donation is made to the organization as a whole,
    # set this field to CourseKeyField.Empty
    course_id = CourseKeyField(max_length=255, db_index=True)

    @classmethod
    @transaction.atomic
    def add_to_order(cls, order, donation_amount, course_id=None, currency='usd'):
        """Add a donation to an order.

        Args:
            order (Order): The order to add this donation to.
            donation_amount (Decimal): The amount the user is donating.


        Keyword Args:
            course_id (CourseKey): If provided, associate this donation with a particular course.
            currency (str): The currency used for the the donation.

        Raises:
            InvalidCartItem: The provided course ID is not valid.

        Returns:
            Donation

        """
        # This will validate the currency but won't actually add the item to the order.
        super(Donation, cls).add_to_order(order, currency=currency)

        # Create a line item description, including the name of the course
        # if this is a per-course donation.
        # This will raise an exception if the course can't be found.
        description = cls._line_item_description(course_id=course_id)

        params = {
            "order": order,
            "user": order.user,
            "status": order.status,
            "qty": 1,
            "unit_cost": donation_amount,
            "currency": currency,
            "line_desc": description
        }

        if course_id is not None:
            params["course_id"] = course_id
            params["donation_type"] = "course"
        else:
            params["donation_type"] = "general"

        return cls.objects.create(**params)

    def purchased_callback(self):
        """Donations do not need to be fulfilled, so this method does nothing."""
        pass

    def generate_receipt_instructions(self):
        """Provide information about tax-deductible donations in the receipt.

        Returns:
            tuple of (Donation, unicode)

        """
        return self.pk_with_subclass, set([self._tax_deduction_msg()])

    def additional_instruction_text(self, **kwargs):
        """Provide information about tax-deductible donations in the confirmation email.

        Returns:
            unicode

        """
        return self._tax_deduction_msg()

    def _tax_deduction_msg(self):
        """Return the translated version of the tax deduction message.

        Returns:
            unicode

        """
        return _(
            u"We greatly appreciate this generous contribution and your support of the {platform_name} mission.  "
            u"This receipt was prepared to support charitable contributions for tax purposes.  "
            u"We confirm that neither goods nor services were provided in exchange for this gift."
        ).format(platform_name=settings.PLATFORM_NAME)

    @classmethod
    def _line_item_description(cls, course_id=None):
        """Create a line-item description for the donation.

        Includes the course display name if provided.

        Keyword Arguments:
            course_id (CourseKey)

        Raises:
            CourseDoesNotExistException: The course ID is not valid.

        Returns:
            unicode

        """
        # If a course ID is provided, include the display name of the course
        # in the line item description.
        if course_id is not None:
            course = modulestore().get_course(course_id)
            if course is None:
                msg = u"Could not find a course with the ID '{course_id}'".format(course_id=course_id)
                log.error(msg)
                raise CourseDoesNotExistException(
                    _(u"Could not find a course with the ID '{course_id}'").format(course_id=course_id)
                )

            return _(u"Donation for {course}").format(course=course.display_name)

        # The donation is for the organization as a whole, not a specific course
        else:
            return _(u"Donation for {platform_name}").format(platform_name=settings.PLATFORM_NAME)

    @property
    def single_item_receipt_context(self):
        return {
            'receipt_has_donation_item': True,
        }

    def analytics_data(self):
        """Simple function used to construct analytics data for the OrderItem.

        If the donation is associated with a course, additional fields will be populated with
        course information. When no name or category is specified by the implementation, the
        platform name is used as a default value for required event fields, to declare that
        the Order is specific to the platform, rather than a specific product name or category.

        Returns
            A dictionary containing analytics data for this OrderItem.

        """
        data = super(Donation, self).analytics_data()
        if self.course_id != CourseKeyField.Empty:
            data['name'] = unicode(self.course_id)
            data['category'] = unicode(self.course_id.org)
        else:
            data['name'] = settings.PLATFORM_NAME
            data['category'] = settings.PLATFORM_NAME
        return data

    @property
    def pdf_receipt_display_name(self):
        """
            How to display this item on a PDF printed receipt file.
        """
        return self._line_item_description(course_id=self.course_id)
