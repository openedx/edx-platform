"""
E-commerce Tab Instructor Dashboard Coupons Operations views
"""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext as _
from util.json_request import JsonResponse
from django.http import HttpResponse, HttpResponseNotFound
from shoppingcart.models import Coupon

import logging

log = logging.getLogger(__name__)


@require_POST
@login_required
def remove_coupon(request):
    """
    remove the coupon against the coupon id
    set the coupon is_active flag to false
    """
    coupon_id = request.REQUEST.get('id', None)
    if not coupon_id:
        context = {
            'success': False,
            'message': _('coupon id is None')
        }
        return JsonResponse(context)

    try:
        coupon = Coupon.objects.get(id=coupon_id)
    except ObjectDoesNotExist:
        context = {
            'success': False,
            'message': _('coupon with the coupon id ({coupon_id}) DoesNotExist').format(coupon_id=coupon_id)
        }
        return JsonResponse(context)
    if coupon.is_active:
        coupon.is_active = False
        coupon.save()
        context = {
            'success': True,
            'message': _('coupon with the coupon id ({coupon_id}) updated successfully'.format(coupon_id=coupon_id))
        }
    else:
        context = {
            'success': False,
            'message': _('coupon with the coupon id ({coupon_id}) is already inactive'.format(coupon_id=coupon_id))
        }
    return JsonResponse(context)


@require_POST
@login_required
def add_coupon(request):
    """
    add coupon in the Coupons Table
    """
    code = request.REQUEST.get('code')

    # check if the code is already in the Coupons Table and active
    coupon = Coupon.objects.filter(is_active=True, code=code)

    if coupon:
        return HttpResponseNotFound(_("coupon with the coupon code ({code}) already exist").format(code=code))
    else:
        description = request.REQUEST.get('description')
        course_id = request.REQUEST.get('course_id')
        discount = request.REQUEST.get('discount')
        coupon = Coupon(
            code=code, description=description, course_id=course_id,
            percentage_discount=discount, created_by_id=request.user.id
        )
        coupon.save()
        return HttpResponse(_("coupon with the coupon code ({code}) added successfully").format(code=code))


@require_POST
@login_required
def update_coupon(request):
    """
    update the coupon object in the database
    """
    coupon_id = request.REQUEST.get('coupon_id', None)
    if not coupon_id:
        return HttpResponseNotFound(_("coupon id not found"))

    try:
        coupon = Coupon.objects.get(pk=coupon_id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound(_("coupon with the coupon id ({coupon_id}) DoesNotExist".format(coupon_id=coupon_id)))

    code = request.REQUEST.get('code')
    filtered_coupons = Coupons.objects.filter(~Q(id=coupon_id), code=code, is_active=True)

    if filtered_coupons:
        return HttpResponseNotFound(_("coupon with the coupon id ({coupon_id}) already exists").format(coupon_id=coupon_id))
    else:
        description = request.REQUEST.get('description')
        course_id = request.REQUEST.get('course_id')
        discount = request.REQUEST.get('discount')
        coupon.code = code
        coupon.description = description
        coupon.course_id = course_id
        coupon.percentage_discount = discount
        coupon.save()

    return HttpResponse(_("coupon with the coupon id ({coupon_id}) updated Successfully".format(coupon_id=coupon_id)))


@require_POST
@login_required
def get_coupon_info(request):
    """
    get the coupon information to display in the pop up form
    """
    coupon_id = request.REQUEST.get('id', None)
    if not coupon_id:
        return JsonResponse({
            'message': _("coupon id not found")
        }, status=400)  # status code 400: Bad Request

    try:
        coupon = Coupon.objects.get(id=coupon_id)
    except ObjectDoesNotExist:
        return JsonResponse({
            'message': _("coupon with the coupon id ({coupon_id}) DoesNotExist".format(coupon_id=coupon_id))
        }, status=400)  # status code 400: Bad Request

    if not coupon.is_active:
        return JsonResponse({
            'message': _("coupon with the coupon id ({coupon_id}) is already inactive".format(coupon_id=coupon_id))
        }, status=400)  # status code 400: Bad Request

    return JsonResponse({
        'coupon_code': coupon.code,
        'coupon_description': coupon.description,
        'coupon_course_id': coupon.course_id.to_deprecated_string(),
        'coupon_discount': coupon.percentage_discount,
        'message': 'coupon with the coupon id ({coupon_id}) updated successfully'.format(coupon_id=coupon_id)
    })  # status code 200: OK by default
