import pytz
import logging
from datetime  import datetime
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from courseware.courses import course_image_url, get_course_about_section
from student.views import course_from_id
from student.models import CourseEnrollmentAllowed, CourseEnrollment
from statsd import statsd
log = logging.getLogger("shoppingcart")

ORDER_STATUSES = (
    ('cart', 'cart'),
    ('purchased', 'purchased'),
    ('refunded', 'refunded'),  # Not used for now
)

class Order(models.Model):
    """
    This is the model for an order.  Before purchase, an Order and its related OrderItems are used
    as the shopping cart.
    FOR ANY USER, THERE SHOULD ONLY EVER BE ZERO OR ONE ORDER WITH STATUS='cart'.
    """
    user = models.ForeignKey(User, db_index=True)
    status = models.CharField(max_length=32, default='cart', choices=ORDER_STATUSES)
    purchase_time = models.DateTimeField(null=True, blank=True)
    # Now we store data needed to generate a reasonable receipt
    # These fields only make sense after the purchase
    bill_to_first = models.CharField(max_length=64, null=True, blank=True)
    bill_to_last = models.CharField(max_length=64, null=True, blank=True)
    bill_to_street1 = models.CharField(max_length=128, null=True, blank=True)
    bill_to_street2 = models.CharField(max_length=128, null=True, blank=True)
    bill_to_city = models.CharField(max_length=64, null=True, blank=True)
    bill_to_state = models.CharField(max_length=8, null=True, blank=True)
    bill_to_postalcode = models.CharField(max_length=16, null=True, blank=True)
    bill_to_country = models.CharField(max_length=64, null=True, blank=True)
    bill_to_ccnum = models.CharField(max_length=8, null=True, blank=True) # last 4 digits
    bill_to_cardtype = models.CharField(max_length=32, null=True, blank=True)
    # a JSON dump of the CC processor response, for completeness
    processor_reply_dump = models.TextField(null=True, blank=True)

    @classmethod
    def get_cart_for_user(cls, user):
        """
        Always use this to preserve the property that at most 1 order per user has status = 'cart'
        """
        order, created = cls.objects.get_or_create(user=user, status='cart')
        return order

    @property
    def total_cost(self):
        return sum([i.line_cost for i in self.orderitem_set.filter(status=self.status)])

    @property
    def currency(self):
        """Assumes that all cart items are in the same currency"""
        items = self.orderitem_set.all()
        if not items:
            return 'usd'
        else:
            return items[0].currency

    def purchase(self, first='', last='', street1='', street2='', city='', state='', postalcode='',
                 country='', ccnum='', cardtype='', processor_reply_dump=''):
        """
        Call to mark this order as purchased.  Iterates through its OrderItems and calls
        their purchased_callback
        """
        self.status = 'purchased'
        self.purchase_time = datetime.now(pytz.utc)
        self.bill_to_first = first
        self.bill_to_last = last
        self.bill_to_street1 = street1
        self.bill_to_street2 = street2
        self.bill_to_city = city
        self.bill_to_state = state
        self.bill_to_postalcode = postalcode
        self.bill_to_country = country
        self.bill_to_ccnum = ccnum
        self.bill_to_cardtype = cardtype
        self.processor_reply_dump = processor_reply_dump
        self.save()
        for item in self.orderitem_set.all():
            item.status = 'purchased'
            item.purchased_callback()
            item.save()


class OrderItem(models.Model):
    """
    This is the basic interface for order items.
    Order items are line items that fill up the shopping carts and orders.

    Each implementation of OrderItem should provide its own purchased_callback as
    a method.
    """
    order = models.ForeignKey(Order, db_index=True)
    # this is denormalized, but convenient for SQL queries for reports, etc. user should always be = order.user
    user = models.ForeignKey(User, db_index=True)
    # this is denormalized, but convenient for SQL queries for reports, etc. status should always be = order.status
    status = models.CharField(max_length=32, default='cart', choices=ORDER_STATUSES)
    qty = models.IntegerField(default=1)
    unit_cost = models.FloatField(default=0.0)
    line_cost = models.FloatField(default=0.0) # qty * unit_cost
    line_desc = models.CharField(default="Misc. Item", max_length=1024)
    currency = models.CharField(default="usd", max_length=8) # lower case ISO currency codes

    def add_to_order(self, *args, **kwargs):
        """
        A suggested convenience function for subclasses.
        """
        raise NotImplementedError

    def purchased_callback(self):
        """
        This is called on each inventory item in the shopping cart when the
        purchase goes through.

        NOTE: We want to provide facilities for doing something like
        for item in OrderItem.objects.filter(order_id=order_id):
            item.purchased_callback()

        Unfortunately the QuerySet used determines the class to be OrderItem, and not its most specific
        subclasses.  That means this parent class implementation of purchased_callback needs to act as
        a dispatcher to call the callback the proper subclasses, and as such it needs to know about all subclasses.
        So please add
        """
        for classname, lc_classname in ORDER_ITEM_SUBTYPES:
            try:
                sub_instance = getattr(self,lc_classname)
                sub_instance.purchased_callback()
            except (ObjectDoesNotExist, AttributeError):
                log.exception('Cannot call purchase_callback on non-existent subclass attribute {0} of OrderItem'\
                              .format(lc_classname))
                pass

# Each entry is a tuple of ('ModelName', 'lower_case_model_name')
# See https://docs.djangoproject.com/en/1.4/topics/db/models/#multi-table-inheritance for
# PLEASE KEEP THIS LIST UP_TO_DATE WITH THE SUBCLASSES OF OrderItem
ORDER_ITEM_SUBTYPES = [
    ('PaidCourseRegistration', 'paidcourseregistration')
]



class PaidCourseRegistration(OrderItem):
    """
    This is an inventory item for paying for a course registration
    """
    course_id = models.CharField(max_length=128, db_index=True)

    @classmethod
    def add_to_order(cls, order, course_id, cost, currency='usd'):
        """
        A standardized way to create these objects, with sensible defaults filled in.
        Will update the cost if called on an order that already carries the course.

        Returns the order item
        """
        # TODO: Possibly add checking for whether student is already enrolled in course
        course = course_from_id(course_id)  # actually fetch the course to make sure it exists, use this to
                                            # throw errors if it doesn't
        item, created = cls.objects.get_or_create(order=order, user=order.user, course_id=course_id)
        item.status = order.status
        item.qty = 1
        item.unit_cost = cost
        item.line_cost = cost
        item.line_desc = 'Registration for Course: {0}'.format(get_course_about_section(course, "title"))
        item.currency = currency
        item.save()
        return item

    def purchased_callback(self):
        """
        When purchased, this should enroll the user in the course.  We are assuming that
        course settings for enrollment date are configured such that only if the (user.email, course_id) pair is found in
        CourseEnrollmentAllowed will the user be allowed to enroll.  Otherwise requiring payment
        would in fact be quite silly since there's a clear back door.
        """
        course = course_from_id(self.course_id)  # actually fetch the course to make sure it exists, use this to
                                                 # throw errors if it doesn't
        # use get_or_create here to gracefully handle case where the user is already enrolled in the course, for
        # whatever reason.
        # Don't really need to create CourseEnrollmentAllowed object, but doing it for bookkeeping and consistency
        # with rest of codebase.
        CourseEnrollmentAllowed.objects.get_or_create(email=self.user.email, course_id=self.course_id, auto_enroll=True)
        CourseEnrollment.objects.get_or_create(user=self.user, course_id=self.course_id)

        log.info("Enrolled {0} in paid course {1}, paid ${2}".format(self.user.email, self.course_id, self.line_cost))
        org, course_num, run = self.course_id.split("/")
        statsd.increment("shoppingcart.PaidCourseRegistration.purchased_callback.enrollment",
                         tags=["org:{0}".format(org),
                               "course:{0}".format(course_num),
                               "run:{0}".format(run)])
