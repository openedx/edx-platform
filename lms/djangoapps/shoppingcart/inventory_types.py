import logging
from django.contrib.auth.models import User
from student.views import course_from_id
from student.models import CourseEnrollmentAllowed, CourseEnrollment
from statsd import statsd

log = logging.getLogger("shoppingcart")

class InventoryItem(object):
    """
    This is the abstract interface for inventory items.
    Inventory items are things that fill up the shopping cart.

    Each implementation of InventoryItem should have purchased_callback as
    a method and data attributes as defined in __init__ below
    """
    def __init__(self):
        # Set up default data attribute values
        self.qty = 1
        self.unit_cost = 0  # in dollars
        self.line_cost = 0  # qty * unit_cost
        self.line_desc = "Misc Item"

    def purchased_callback(self, user_id):
        """
        This is called on each inventory item in the shopping cart when the
        purchase goes through.  The parameter provided is the id of the user who
        made the purchase.
        """
        raise NotImplementedError


class PaidCourseRegistration(InventoryItem):
    """
    This is an inventory item for paying for a course registration
    """
    def __init__(self, course_id, unit_cost):
        course = course_from_id(course_id)  # actually fetch the course to make sure it exists, use this to
                                            # throw errors if it doesn't
        self.qty = 1
        self.unit_cost = unit_cost
        self.line_cost = unit_cost
        self.course_id = course_id
        self.line_desc = "Registration for Course {0}".format(course_id)

    def purchased_callback(self, user_id):
        """
        When purchased, this should enroll the user in the course.  We are assuming that
        course settings for enrollment date are configured such that only if the (user.email, course_id) pair is found in
        CourseEnrollmentAllowed will the user be allowed to enroll.  Otherwise requiring payment
        would in fact be quite silly since there's a clear back door.
        """
        user = User.objects.get(id=user_id)
        course = course_from_id(self.course_id)  # actually fetch the course to make sure it exists, use this to
                                                 # throw errors if it doesn't
        # use get_or_create here to gracefully handle case where the user is already enrolled in the course, for
        # whatever reason.
        # Don't really need to create CourseEnrollmentAllowed object, but doing it for bookkeeping and consistency
        # with rest of codebase.
        CourseEnrollmentAllowed.objects.get_or_create(email=user.email, course_id=self.course_id, auto_enroll=True)
        CourseEnrollment.objects.get_or_create(user=user, course_id=self.course_id)

        log.info("Enrolled {0} in paid course {1}, paid ${2}".format(user.email, self.course_id, self.line_cost))
        org, course_num, run = self.course_id.split("/")
        statsd.increment("shoppingcart.PaidCourseRegistration.purchased_callback.enrollment",
                         tags=["org:{0}".format(org),
                               "course:{0}".format(course_num),
                               "run:{0}".format(run)])
