"""
Views for manual refunds in the student support UI.

This interface is used by the support team to track refunds
entered manually in CyberSource (our payment gateway).

DEPRECATION WARNING:
We are currently in the process of replacing lms/djangoapps/shoppingcart
with an E-Commerce service that supports automatic refunds.  Once that
transition is complete, we can remove this view.

"""
import logging

from django.contrib.auth.models import User
from django.views.generic.edit import FormView
from django.utils.translation import ugettext as _
from django.http import HttpResponseRedirect
from django.contrib import messages
from django import forms
from django.utils.decorators import method_decorator

from student.models import CourseEnrollment
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from support.decorators import require_support_permission

log = logging.getLogger(__name__)


class RefundForm(forms.Form):
    """
    Form for manual refunds
    """
    user = forms.EmailField(label=_("Email Address"), required=True)
    course_id = forms.CharField(label=_("Course ID"), required=True)
    confirmed = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_user(self):
        """
        validate user field
        """
        user_email = self.cleaned_data['user']
        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise forms.ValidationError(_("User not found"))
        return user

    def clean_course_id(self):
        """
        validate course id field
        """
        course_id = self.cleaned_data['course_id']
        try:
            course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            try:
                course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
            except InvalidKeyError:
                raise forms.ValidationError(_("Invalid course id"))
        return course_key

    def clean(self):
        """
        clean form
        """
        user, course_id = self.cleaned_data.get('user'), self.cleaned_data.get('course_id')
        if user and course_id:
            self.cleaned_data['enrollment'] = enrollment = CourseEnrollment.get_or_create_enrollment(user, course_id)
            if enrollment.refundable():
                msg = _("Course {course_id} not past the refund window.").format(course_id=course_id)
                raise forms.ValidationError(msg)
            try:
                self.cleaned_data['cert'] = enrollment.certificateitem_set.filter(
                    mode='verified',
                    status='purchased'
                )[0]
            except IndexError:
                msg = _("No order found for {user} in course {course_id}").format(user=user, course_id=course_id)
                raise forms.ValidationError(msg)
        return self.cleaned_data

    def is_valid(self):
        """
        returns whether form is valid
        """
        is_valid = super(RefundForm, self).is_valid()
        if is_valid and self.cleaned_data.get('confirmed') != 'true':
            # this is a two-step form: first look up the data, then issue the refund.
            # first time through, set the hidden "confirmed" field to true and then redisplay the form
            # second time through, do the unenrollment/refund.
            data = dict(self.data.items())
            self.cleaned_data['confirmed'] = data['confirmed'] = 'true'
            self.data = data
            is_valid = False
        return is_valid


class RefundSupportView(FormView):
    """
    Refund form view
    """
    template_name = 'support/refund.html'
    form_class = RefundForm
    success_url = '/support/'

    @method_decorator(require_support_permission)
    def dispatch(self, *args, **kwargs):
        return super(RefundSupportView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        extra context data to add to page
        """
        form = getattr(kwargs['form'], 'cleaned_data', {})
        if form.get('confirmed') == 'true':
            kwargs['cert'] = form.get('cert')
            kwargs['enrollment'] = form.get('enrollment')
        return kwargs

    def form_valid(self, form):
        """
        unenrolls student, issues refund
        """
        user = form.cleaned_data['user']
        course_id = form.cleaned_data['course_id']
        enrollment = form.cleaned_data['enrollment']
        cert = form.cleaned_data['cert']
        enrollment.can_refund = True
        enrollment.update_enrollment(is_active=False)

        log.info(u"%s manually refunded %s %s", self.request.user, user, course_id)
        messages.success(
            self.request,
            _("Unenrolled {user} from {course_id}").format(
                user=user,
                course_id=course_id
            )
        )
        messages.success(
            self.request,
            _("Refunded {cost} for order id {order_id}").format(
                cost=cert.unit_cost,
                order_id=cert.order.id
            )
        )
        return HttpResponseRedirect('/support/refund/')
