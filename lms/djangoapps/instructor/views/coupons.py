"""
E-commerce Tab Instructor Dashboard Coupons Operations views
"""
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.http import require_POST
from django.utils.translation import ugettext as _
from util.json_request import JsonResponse
from shoppingcart.models import Coupon, CourseRegistrationCode
from opaque_keys.edx.locations import SlashSeparatedCourseKey
import datetime
import pytz
import logging

log = logging.getLogger(__name__)


@require_POST
@login_required
def remove_coupon(request, course_id):  # pylint: disable=unused-argument
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
def add_coupon(request, course_id):
    """
    add coupon in the Coupons Table
    """
    code = request.POST.get('code')

    # check if the code is already in the Coupons Table and active
    try:
        course_id = SlashSeparatedCourseKey.from_deprecated_string(course_id)
        coupon = Coupon.objects.get(is_active=True, code=code, course_id=course_id)
    except Coupon.DoesNotExist:
        # check if the coupon code is in the CourseRegistrationCode Table
        course_registration_code = CourseRegistrationCode.objects.filter(code=code)
        if course_registration_code:
            return JsonResponse(
                {'message': _("The code ({code}) that you have tried to define is already in use as a registration code").format(code=code)},
                status=400)  # status code 400: Bad Request

        description = request.POST.get('description')
        course_id = request.POST.get('course_id')
        try:
            discount = int(request.POST.get('discount'))
        except ValueError:
            return JsonResponse({
                'message': _("Please Enter the Integer Value for Coupon Discount")
            }, status=400)  # status code 400: Bad Request

        if discount > 100 or discount < 0:
            return JsonResponse({
                'message': _("Please Enter the Coupon Discount Value Less than or Equal to 100")
            }, status=400)  # status code 400: Bad Request
        expiration_date = None
        if request.POST.get('expiration_date'):
            expiration_date = request.POST.get('expiration_date')
            try:
                expiration_date = datetime.datetime.strptime(expiration_date, "%m/%d/%Y").replace(tzinfo=pytz.UTC) + datetime.timedelta(days=1)
            except ValueError:
                return JsonResponse({
                    'message': _("Please enter the date in this format i-e month/day/year")
                }, status=400)  # status code 400: Bad Request

        coupon = Coupon(
            code=code, description=description,
            course_id=course_id,
            percentage_discount=discount,
            created_by_id=request.user.id,
            expiration_date=expiration_date
        )
        coupon.save()
        return JsonResponse(
            {'message': _("coupon with the coupon code ({code}) added successfully").format(code=code)}
        )

    if coupon:
        return JsonResponse(
            {'message': _("coupon with the coupon code ({code}) already exists for this course").format(code=code)},
            status=400)  # status code 400: Bad Request


@require_POST
@login_required
def update_coupon(request, course_id):  # pylint: disable=unused-argument
    """
    update the coupon object in the database
    """
    coupon_id = request.POST.get('coupon_id', None)
    if not coupon_id:
        return JsonResponse({'message': _("coupon id not found")}, status=400)  # status code 400: Bad Request

    try:
        coupon = Coupon.objects.get(pk=coupon_id)
    except ObjectDoesNotExist:
        return JsonResponse(
            {'message': _("coupon with the coupon id ({coupon_id}) DoesNotExist").format(coupon_id=coupon_id)},
            status=400)  # status code 400: Bad Request

    description = request.POST.get('description')
    coupon.description = description
    coupon.save()
    return JsonResponse(
        {'message': _("coupon with the coupon id ({coupon_id}) updated Successfully").format(coupon_id=coupon_id)}
    )


@require_POST
@login_required
def get_coupon_info(request, course_id):  # pylint: disable=unused-argument
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

    expiry_date = coupon.display_expiry_date
    return JsonResponse({
        'coupon_code': coupon.code,
        'coupon_description': coupon.description,
        'coupon_course_id': coupon.course_id.to_deprecated_string(),
        'coupon_discount': coupon.percentage_discount,
        'expiry_date': expiry_date,
        'message': _('coupon with the coupon id ({coupon_id}) updated successfully').format(coupon_id=coupon_id)
    })  # status code 200: OK by default
