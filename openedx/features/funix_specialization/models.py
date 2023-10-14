from django.db import models

class FunixSpecialization (models.Model):
    spec_name =   models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.spec_name
    
    @classmethod
    def create_specialization_funix (cls,spec_name, user_id ):

        existCert = FunixSpecialization.objects.filter(spec_name = spec_name).exists()
        if existCert :
            return None
        else :
            return FunixSpecialization.objects.create(spec_name = spec_name , user_id = user_id)
    def getAllSpec ():
        return FunixSpecialization.objects.all()
        

class FunixSpecializationCourse (models.Model):
    course_id = models.CharField(max_length=255)
    spec =  models.ForeignKey(FunixSpecialization, on_delete=models.CASCADE)
    user_id = models.CharField(max_length=255)

    def __str__(self):
        return self.course_id
    @classmethod
    def setSpecializationCourseFunix (cls,course_id, spec_id, user_id):
        existCert = FunixSpecializationCourse.objects.filter(course_id = course_id, spec = spec_id ).exists()
        if existCert:
            return None
        else :
            return FunixSpecializationCourse.objects.create(course_id=course_id, spec_id = spec_id, user_id = user_id)
        
    @classmethod
    def removeSpecializationCourseFunix (cls,course_id, spec_id):
        return FunixSpecializationCourse.objects.filter(course_id = course_id, spec_id=spec_id).delete()
    
    @classmethod
    def getSpecializationCourse (cls, course_id):
        return FunixSpecializationCourse.objects.filter(course_id=course_id)