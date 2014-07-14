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
from shoppingcart.models import Coupon, CourseRegistrationCode

import logging

log = logging.getLogger(__name__)


@require_POST
@login_required
def remove_coupon(request, course_id):  # pylint: disable=W0613
    """
    remove the coupon against the coupon id
    set the coupon is_active flag to false
    """
    coupon_id = request.POST.get('id', None)
    if not coupon_id:
        return JsonResponse({
            'message': _('coupon id is None')
        }, status=400)  # status code 400: Bad Request

    try:
        coupon = Coupon.objects.get(id=coupon_id)
    except ObjectDoesNotExist:
        return JsonResponse({
            'message': _('coupon with the coupon id ({coupon_id}) DoesNotExist').format(coupon_id=coupon_id)
        }, status=400)  # status code 400: Bad Request
    if not coupon.is_active:
        return JsonResponse({
            'message': _('coupon with the coupon id ({coupon_id}) is already inactive').format(coupon_id=coupon_id)
        }, status=400)  # status code 400: Bad Request
    coupon.is_active = False
    coupon.save()
    return JsonResponse({
        'message': _('coupon with the coupon id ({coupon_id}) updated successfully').format(coupon_id=coupon_id)
    })  # status code 200: OK by default


@require_POST
@login_required
def add_coupon(request, course_id):  # pylint: disable=W0613
    """
    add coupon in the Coupons Table
    """
    code = request.POST.get('code')

    # check if the code is already in the Coupons Table and active
    coupon = Coupon.objects.filter(is_active=True, code=code)

    if coupon:
        return HttpResponseNotFound(_("coupon with the coupon code ({code}) already exist").format(code=code))

     # check if the coupon code is in the CourseRegistrationCode Table
    course_registration_code = CourseRegistrationCode.objects.filter(code=code)
    if course_registration_code:
        return HttpResponseNotFound(_(
            "The code ({code}) that you have tried to define is already in use as a registration code").format(code=code)
        )

    description = request.POST.get('description')
    course_id = request.POST.get('course_id')
    try:
        discount = int(request.POST.get('discount'))
    except ValueError:
        return HttpResponseNotFound(_("Please Enter the Integer Value for Coupon Discount"))
    if discount > 100:
        return HttpResponseNotFound(_("Please Enter the Coupon Discount Value Less than or Equal to 100"))
    coupon = Coupon(
        code=code, description=description, course_id=course_id,
        percentage_discount=discount, created_by_id=request.user.id
    )
    coupon.save()
    return HttpResponse(_("coupon with the coupon code ({code}) added successfully").format(code=code))


@require_POST
@login_required
def update_coupon(request, course_id):  # pylint: disable=W0613
    """
    update the coupon object in the database
    """
    coupon_id = request.POST.get('coupon_id', None)
    if not coupon_id:
        return HttpResponseNotFound(_("coupon id not found"))

    try:
        coupon = Coupon.objects.get(pk=coupon_id)
    except ObjectDoesNotExist:
        return HttpResponseNotFound(_("coupon with the coupon id ({coupon_id}) DoesNotExist").format(coupon_id=coupon_id))

    code = request.POST.get('code')
    filtered_coupons = Coupon.objects.filter(~Q(id=coupon_id), code=code, is_active=True)

    if filtered_coupons:
        return HttpResponseNotFound(_("coupon with the coupon id ({coupon_id}) already exists").format(coupon_id=coupon_id))

    # check if the coupon code is in the CourseRegistrationCode Table
    course_registration_code = CourseRegistrationCode.objects.filter(code=code)
    if course_registration_code:
        return HttpResponseNotFound(_(
            "The code ({code}) that you have tried to define is already in use as a registration code").format(code=code)
        )

    description = request.POST.get('description')
    course_id = request.POST.get('course_id')
    try:
        discount = int(request.POST.get('discount'))
    except ValueError:
        return HttpResponseNotFound(_("Please Enter the Integer Value for Coupon Discount"))
    if discount > 100:
        return HttpResponseNotFound(_("Please Enter the Coupon Discount Value Less than or Equal to 100"))
    coupon.code = code
    coupon.description = description
    coupon.course_id = course_id
    coupon.percentage_discount = discount
    coupon.save()
    return HttpResponse(_("coupon with the coupon id ({coupon_id}) updated Successfully").format(coupon_id=coupon_id))


@require_POST
@login_required
def get_coupon_info(request, course_id):  # pylint: disable=W0613
    """
    get the coupon information to display in the pop up form
    """
    coupon_id = request.POST.get('id', None)
    if not coupon_id:
        return JsonResponse({
            'message': _("coupon id not found")
        }, status=400)  # status code 400: Bad Request

    try:
        coupon = Coupon.objects.get(id=coupon_id)
    except ObjectDoesNotExist:
        return JsonResponse({
            'message': _("coupon with the coupon id ({coupon_id}) DoesNotExist").format(coupon_id=coupon_id)
        }, status=400)  # status code 400: Bad Request

    if not coupon.is_active:
        return JsonResponse({
            'message': _("coupon with the coupon id ({coupon_id}) is already inactive").format(coupon_id=coupon_id)
        }, status=400)  # status code 400: Bad Request

    return JsonResponse({
        'coupon_code': coupon.code,
        'coupon_description': coupon.description,
        'coupon_course_id': coupon.course_id.to_deprecated_string(),
        'coupon_discount': coupon.percentage_discount,
        'message': _('coupon with the coupon id ({coupon_id}) updated successfully').format(coupon_id=coupon_id)
    })  # status code 200: OK by default
