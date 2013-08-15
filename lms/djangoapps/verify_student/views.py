"""


"""
from mitxmako.shortcuts import render_to_response

# @login_required
def start_or_resume_attempt(request):
    """
    If they've already started a PhotoVerificationAttempt, we move to wherever
    they are in that process. If they've completed one, then we skip straight
    to payment.
    """
    pass

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
