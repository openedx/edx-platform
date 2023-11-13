import json
import logging
from django.http import HttpResponse, HttpResponseNotFound
from django.http import JsonResponse
from openedx.core.djangoapps.user_authn.views.registration_form import AccountCreationForm
from common.djangoapps.student.helpers import (
    AccountValidationError,
    authenticate_new_user,
    create_or_set_user_attribute_created_on_site,
    do_create_account
)

from common.djangoapps.student.models import (  # lint-amnesty, pylint: disable=unused-import
    CourseEnrollmentAllowed,
    LoginFailures,
    ManualEnrollmentAudit,
    PendingEmailChange,
    PendingNameChange,
    User,
    UserProfile,
    get_potentially_retired_user_by_username,
    get_retired_email_by_email,
    get_retired_username_by_username,
    is_email_retired,
    is_username_retired
)

def create_user_view(request): 
    if request.method != 'POST':
        return JsonResponse({
            "message": "Not allowed method"
        }, status=405)

    data = json.loads(request.body)
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('full_name')

    try:
        user = User.objects.get(email=email)
        return JsonResponse({
            "message": f"User with email {email} already exists."
        }, status=400)
    except User.DoesNotExist:
        pass
    except Exception as e: 
        logging.error(str(e))
        return JsonResponse({
            "message": "Internal Server Error", 
        })

    try:
        user = User.objects.get(username=username)
        return JsonResponse({
            "message": f"User with username {username} already exists."
        }, status=400)
    except User.DoesNotExist: 
        pass
    except Exception as e: 
        logging.error(str(e))
        return JsonResponse({
            "message": "Internal Server Error"
        })

    form = AccountCreationForm(
        data={
            'username': username,
            'email': email,
            'password': password,
            'name': full_name,
        },
        tos_required=False
    )

    try:
        user, profile, reg = do_create_account(form)
        user.is_active = True
        user.save()

        return JsonResponse({
            "message":  "success", 
            "data": {
                "username": user.username,
                "email": user.email
            }
        })
    except Exception as e:
        return JsonResponse({
            "message": str(e),
        }, status=500)


def update_user_password(request): 
    if request.method != 'POST': 
        return JsonResponse({
            "message": "Not allowed method."
        })

    data = json.loads(request.body)
    email = data.get("email")
    password = data.get("password")
    new_password = data.get("new_password")
    
    try:
        user = User.objects.get(email=email)
        password_matches = user.check_password(password)
        if password_matches: 
            try:
                user.set_password(new_password)
                user.save()
                return JsonResponse({
                    "message": f"Updated successfully new password for user with email {email}."
                })
            except Exception as e:
                logging.error(str(e))
                return JsonResponse({
                    "message": "Internal Server Error"
                }, status=500)
        else:
            return JsonResponse({
                "message": "Invalid password."
            }, status=400)
    except User.DoesNotExist:
        return JsonResponse({
            "message": f"Not found user with email {email}"
        }, status=400)

    except Exception as e: 
        logging.error(str(e))
        return JsonResponse({
            "message": "Internal Server Error"
        }, status=500)