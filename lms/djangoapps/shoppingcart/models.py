import pytz
import logging
from datetime  import datetime
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
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
    THERE SHOULD ONLY EVER BE ZERO OR ONE ORDER WITH STATUS='cart' PER USER.
    """
    user = models.ForeignKey(User, db_index=True)
    status = models.CharField(max_length=32, default='cart', choices=ORDER_STATUSES)
    # Because we allow an external service to tell us when something is purchased, and our order numbers
    # are their pk and therefore predicatble, let's protect against
    # forged/replayed replies with a nonce.
    nonce = models.CharField(max_length=128)
    purchase_time = models.DateTimeField(null=True, blank=True)

    @classmethod
    def get_cart_for_user(cls, user):
        """
        Use this to enforce the property that at most 1 order per user has status = 'cart'
        """
        order, created = cls.objects.get_or_create(user=user, status='cart')
        return order

    @property
    def total_cost(self):
        return sum([i.line_cost for i in self.orderitem_set.all()])

    def purchase(self):
        """
        Call to mark this order as purchased.  Iterates through its OrderItems and calls
        their purchased_callback
        """
        self.status = 'purchased'
        self.purchase_time = datetime.now(pytz.utc)
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
    def add_to_order(cls, order, course_id, cost):
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
        item.line_desc = "Registration for Course {0}".format(course_id)
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
