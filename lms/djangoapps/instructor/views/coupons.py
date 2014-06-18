"""
E-commerce Tab Instructor Dashboard COupons Operations views
"""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseNotFound
from shoppingcart.models import Coupons

import json
import logging

log = logging.getLogger(__name__)


@require_POST
@login_required
def remove_coupon(request):
    """
    remove the coupon against the coupon id
    set the coupon is_active flag to false
    """
    coupon_id = request.REQUEST.get('id', '-1')
    try:
        coupon = Coupons.objects.get(id=coupon_id)
        if coupon.created_by == request.user and coupon.is_active:
            coupon.is_active = False
            coupon.save()
            context = {'success': True,
                       'message': _('coupon id={0} updated successfully'.format(coupon_id))}
        else:
            context = {'success': False,
                       'message': _('coupon id={0} is already inactive or request made by Anonymous User'.format(coupon_id))}
    except ObjectDoesNotExist:
        context = {'success': False,
                   'message': _('Cannot remove coupon Coupon id={0}. DoesNotExist or coupon is already deleted'.format(coupon_id))}
    return HttpResponse(json.dumps(context), content_type="application/json")


@require_POST
@login_required
def add_coupon(request):
    """
    add coupon in the Coupons Table
    """
    code = request.REQUEST.get('code')
    try:
        coupon = Coupons.objects.filter(is_active=True).get(code=code)
    except Coupons.DoesNotExist:
        coupon = None
    if coupon:
        return HttpResponseNotFound(_("Cannot add Coupon. Coupon code Already Exist"))
    else:
        description = request.REQUEST.get('description')
        course_id = request.REQUEST.get('course_id')
        discount = request.REQUEST.get('discount')
        coupon = Coupons(code=code, description=description, course_id=course_id, percentage_discount=discount,
                         created_by_id=request.user.id)
        coupon.save()
        return HttpResponse()


@require_POST
@login_required
def update_coupon(request):
    """
    update the coupon object in the database
    """
    coupon_id = request.REQUEST.get('coupon_id')
    try:
        coupon = Coupons.objects.get(pk=coupon_id)
        code = request.REQUEST.get('code')
        c_code = Coupons.objects.filter(code=code).filter(is_active=True).filter(~Q(id=coupon_id))
        if c_code:
            return HttpResponseNotFound(_("Cannot Update Coupon. Coupon code Already Exist"))
        else:
            description = request.REQUEST.get('description')
            course_id = request.REQUEST.get('course_id')
            discount = request.REQUEST.get('discount')
            coupon.code = code
            coupon.description = description
            coupon.course_id = course_id
            coupon.percentage_discount = discount
            coupon.save()
    except ObjectDoesNotExist:
        return HttpResponseNotFound(_("Coupon does not exist against coupon {0}".format(coupon_id)))
    return HttpResponse(_("Coupon coupon {0} updated".format(coupon_id)))


@require_POST
@login_required
def edit_coupon_info(request):
    """
    get the coupon information to display in the pop up form
    """
    coupon_id = request.REQUEST.get('id', '-1')
    try:
        coupon = Coupons.objects.get(id=coupon_id)
        if coupon.created_by == request.user and coupon.is_active:
            context = {'coupon_code': coupon.code,
                       'coupon_description': coupon.description,
                       'coupon_course_id': coupon.course_id.to_deprecated_string(),
                       'coupon_discount': coupon.percentage_discount,
                       'success': True,
                       'message': 'coupon id={0} fields updated successfully'.format(coupon_id)}
        else:
            context = {'success': False,
                       'message': _("Coupon is not active or request made by Anonymous User")}
    except ObjectDoesNotExist:
        context = {'success': False, 'message': _("Coupon does not exist against coupon {0}".format(coupon_id))}
    return HttpResponse(json.dumps(context), content_type="application/json")
