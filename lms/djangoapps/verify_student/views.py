"""


"""
from mitxmako.shortcuts import render_to_response

from verify_student.models import SoftwareSecurePhotoVerification

# @login_required
def start_or_resume_attempt(request, course_id):
    """
    If they've already started a PhotoVerificationAttempt, we move to wherever
    they are in that process. If they've completed one, then we skip straight
    to payment.
    """
    # If the user has already been verified within the given time period,
    # redirect straight to the payment -- no need to verify again.
    #if SoftwareSecurePhotoVerification.user_is_verified(user):
    #    pass

    attempt = SoftwareSecurePhotoVerification.active_for_user(request.user)
    if not attempt:
        # Redirect to show requirements
        pass

    # if attempt.

def show_requirements(request):
    """This might just be a plain template without a view."""
    context = { "course_id" : "edX/Certs101/2013_Test" }
    return render_to_response("verify_student/show_requirements.html", context)

def face_upload(request):
    context = { "course_id" : "edX/Certs101/2013_Test" }
    return render_to_response("verify_student/face_upload.html", context)

def photo_id_upload(request):
    context = { "course_id" : "edX/Certs101/2013_Test" }
    return render_to_response("verify_student/photo_id_upload.html", context)

def final_verification(request):
    context = { "course_id" : "edX/Certs101/2013_Test" }
    return render_to_response("verify_student/final_verification.html", context)

#

def show_verification_page(request):
    pass

