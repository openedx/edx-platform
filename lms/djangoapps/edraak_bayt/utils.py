from .models import BaytPublishedCertificate

def check_user_publish(user_id, course_id):
    if BaytPublishedCertificate.objects.filter(user_id=user_id, course_id=course_id).count() > 0:
        return True
    else:
        return False