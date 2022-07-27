"""
Serializers for all Course Enrollment related return objects.
"""


from asyncore import read
import logging
# from itsdangerous import Serializer
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore
from lms.djangoapps.courseware.courses import (
    get_course_with_access,get_permission_for_course_about,)
from django.db import transaction

from rest_framework import serializers

from common.djangoapps.course_modes.models import CourseMode , get_course_prices ,format_course_price ,get_cosmetic_display_price
from common.djangoapps.student.models import CourseEnrollment , LiveClassEnrollment , UserProfile , NotifyCallRequest
from openedx.core.djangoapps.content.course_overviews.models import LiveClasses, CourseOverview

from common.djangoapps.split_modulestore_django.models import SplitModulestoreCourseIndex
from django.contrib.auth.models import User 
import datetime

log = logging.getLogger(__name__)


class StringListField(serializers.CharField):
    """Custom Serializer for turning a comma delimited string into a list.

    This field is designed to take a string such as "1,2,3" and turn it into an actual list
    [1,2,3]

    """
    def field_to_native(self, obj, field_name):  # pylint: disable=unused-argument
        """
        Serialize the object's class name.
        """
        if not obj.suggested_prices:
            return []

        items = obj.suggested_prices.split(',')
        return [int(item) for item in items]  


class CourseSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """
    Serialize a course descriptor and related information.
    """

    course_id = serializers.CharField(source="id")
    course_name = serializers.CharField(source="display_name_with_default")
    enrollment_start = serializers.DateTimeField(format=None)
    enrollment_end = serializers.DateTimeField(format=None)
    course_start = serializers.DateTimeField(source="start", format=None)
    course_end = serializers.DateTimeField(source="end", format=None)
    invite_only = serializers.BooleanField(source="invitation_only")
    course_modes = serializers.SerializerMethodField()
    pacing_type = serializers.SerializerMethodField()

    class Meta:
        # For disambiguating within the drf-yasg swagger schema
        ref_name = 'enrollment.Course'

    def __init__(self, *args, **kwargs):
        self.include_expired = kwargs.pop("include_expired", False)
        super().__init__(*args, **kwargs)

    def get_course_modes(self, obj):
        """
        Retrieve course modes associated with the course.
        """
        course_modes = CourseMode.modes_for_course(
            obj.id,
            include_expired=self.include_expired,
            only_selectable=False
        )
        return [
            ModeSerializer(mode).data
            for mode in course_modes
        ]

    def get_pacing_type(self, obj):
        """
        Get a string representation of the course pacing.
        """
        return "Self Paced" if obj.self_paced else "Instructor Paced"


class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """Serializes CourseEnrollment models

    Aggregates all data from the Course Enrollment table, and pulls in the serialization for
    the Course Descriptor and course modes, to give a complete representation of course enrollment.

    """
    #price = serializers.SerializerMethodField()
    course_details = CourseSerializer(source="course_overview")
    #course_live_class= LiveClassesSerializer()

    #live_class_details= serializers.SerializerMethodField()
    user = serializers.SerializerMethodField('get_username')

    # course_price = serializers.CharField()
    # def get_price(self , obj):   #(request, course_id):
    #     price = get_course_prices(
    #         obj.course
    #         )
    #     log.info("____course-Price______", price , obj)
    #     return price 



    def get_username(self, model):
        """Retrieves the username from the associated model."""
        return model.username


    # def get_live_class_details(self , obj):


    #     live_classes = LiveClasses.live_class_for_course(
    #         obj.course_id ,)

    #     return[
    #         LiveClassesDetailsSerializer(classes).data
    #         for classes in live_classes
    #     ]


    class Meta:
        model = CourseEnrollment
        fields = ('id','created', 'mode', 'is_active', 'course_details', 'user' , 'course_price') # , 'live_class_details') #,'live_class_details' ,'course_live_class' ) # , 'price')
        lookup_field = 'username'
        # read_only_fields = ('id')




class LiveClassesSerializer(serializers.ModelSerializer):

    course_id = serializers.CharField(write_only=True , required =False)

    created_by_id = serializers.CharField(source="created_by", read_only=True)

    # course_id = CourseEnrollmentSerializer(read_only=True)

    course = CourseSerializer(read_only=True)



    class Meta:
        
        model = LiveClasses
        
        fields = ('id', 'start_time' ,'end_time' , 'start_date' , 'end_date' , 'room_key' , 'room_name', 'topic_name' , 'client_token', 'meeting_link' ,'created_by_id', 'created_date' , 'days', 'meeting_notes' , 'is_recurrence_meeting' , 'course' , 'course_id')

    def create(self, validated_data ):
        validated_data['created_date']= datetime.datetime.now()
        validated_data['created_by_id']= self.context['user'].id
        return LiveClasses.objects.create(**validated_data)


    def update(self, instance, validated_data):
        super(LiveClassesSerializer, self).update(instance, validated_data)
        return instance 

    def validate(self, data):
        topic_name = data.get('topic_name')
        if topic_name is None:
            raise serializers.ValidationError({"topic_name":"topic_name required"})
        current_date_time = datetime.datetime.now()
        current_date = current_date_time.date()
        current_time = current_date_time.time()
        start_date  = data.get('start_date')
        end_date = data.get('end_date')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        days = data.get('days')
        days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        if start_date and start_time and end_date and end_time is not None:
            if int(float((end_date - start_date).days)/30.5)> 6:
                raise serializers.ValidationError("Live Course should not exceed 6 months.")
            if start_date < current_date :
                raise serializers.ValidationError("Start date and time shouldn't be less than today's date and time ")
            if end_date < start_date:
                raise serializers.ValidationError("End date and time shouldn't be less than start date and time")
        if data.get('is_recurrence_meeting') is not None:
            if data.get('is_recurrence_meeting'):
                if type(days) != list or days == [] :
                    raise serializers.ValidationError("Days should be non empty list")
                if not set(days).issubset(set(days_list)):
                    raise serializers.ValidationError(f"Invalid list of days Should be {days_list}")
        return data 
        


class CourseEnrollmentsApiListSerializer(CourseEnrollmentSerializer):
    """
    Serializes CourseEnrollment model and returns a subset of fields returned
    by the CourseEnrollmentSerializer.
    """
    course_id = serializers.CharField(source='course_overview.id')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop('course_details')

    class Meta(CourseEnrollmentSerializer.Meta):
        fields = CourseEnrollmentSerializer.Meta.fields + ('course_id',)


class ModeSerializer(serializers.Serializer):  # pylint: disable=abstract-method
    """Serializes a course's 'Mode' tuples

    Returns a serialized representation of the modes available for course enrollment. The course
    modes models are designed to return a tuple instead of the model object itself. This serializer
    does not handle the model object itself, but the tuple.

    """
    slug = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length=255)
    min_price = serializers.IntegerField()
    suggested_prices = StringListField(max_length=255)
    currency = serializers.CharField(max_length=8)
    expiration_datetime = serializers.DateTimeField()
    description = serializers.CharField()
    sku = serializers.CharField()
    bulk_sku = serializers.CharField()



# class LiveClassesDetailsSerializer(serializers.Serializer): 

#     start_time = serializers.TimeField()
#     end_time = serializers.TimeField()
#     end_date= serializers.TimeField()
#     room_key = serializers.CharField()
#     room_name = serializers.CharField()
#     topic_name = serializers.CharField()
#     start_date = serializers.DateTimeField()
#     client_token = serializers.CharField()
#     meeting_link = serializers.CharField()
#     created_date = serializers.DateTimeField()
#     created_by = serializers.CharField()
#     meeting_notes = serializers.CharField()
#     is_recurrence_meeting = serializers.BooleanField()



class UserListSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = User
        fields = ('id' , 'username', 'email' , 'is_active', 'is_staff' ,'is_superuser')



class StaffListSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = User
        fields = ('id' , 'username', 'email' ,  'is_staff' )


class STudentUserListSerializer(serializers.ModelSerializer):
    

    class Meta:
        model = User
        fields = ('id' , 'username', 'email' ,  'is_active' ,'first_name' , 'last_name' , 'date_joined')




class UserAttendanceListSerializer(serializers.ModelSerializer):
    
    user = serializers.CharField()


    class Meta:
        model = UserProfile
        fields = ('user','user_attendance')


class LiveClassEnrollmentSerializer(serializers.ModelSerializer):


    class Meta:
        model = LiveClassEnrollment
        fields = ( 'id','user', 'live_class')



 
    def create(self, validated_data):
        instance=LiveClassEnrollment.objects.create(live_class=validated_data.get('live_class'), user=validated_data.get('user') , updated_at = datetime.datetime.now())
        instance.save()
        CourseEnrollment.objects.create(course=instance.live_class.course, user=instance.user, assigned_by=self.context['assigned_by'])
        
        return instance


class LiveClassUserDetailsSerializer(serializers.ModelSerializer):

    #live_class =LiveClassesSerializer(read_only=True)
    user =UserListSerializer( read_only=True)


    class Meta:
        model = LiveClassEnrollment
        fields = ( 'id','user', 'live_class')
        #read_only_fields = ('id',)




class CourseEnrolledUserDetailsSerializer(serializers.ModelSerializer):

    #live_class =LiveClassesSerializer(read_only=True)
    user =UserListSerializer( read_only=True)
    # course = serializers.CharField()




    class Meta:
        model = CourseEnrollment
        fields = ( 'assigned_by' ,'user')
        



class UserLiveClassDetailsSerializer(serializers.ModelSerializer):

    live_class =LiveClassesSerializer(read_only=True)
    # user =UserListSerializer( read_only=True)


    class Meta:
        model = LiveClassEnrollment
        fields = ( 'id','user', 'live_class')
        





class LoginStaffCourseDetailsSerializer(serializers.ModelSerializer):

    # edited_by_id = serializers.CharField()

    class Meta:
        model = SplitModulestoreCourseIndex
        fields = ('org' ,'course_id' ,'edited_by_id' ,'edited_on' ,'last_update' )





class LiveClassUserTotalAttendanceSerializer(serializers.ModelSerializer):


    user = serializers.CharField()
    
    class Meta:
        model = LiveClassEnrollment
        fields= ('id','liveclass_attendance', 'user' , )


class UserRequestCallSerializer(serializers.ModelSerializer):


    
    class Meta:
        model = NotifyCallRequest
        fields= ('requested_to', 'messeage' , 'requested_at' , 'seen')


    def create(self, validated_data ):
        validated_data['requested_at']= datetime.datetime.now()
        validated_data['requested_by_id']= self.context['user'].id
        return NotifyCallRequest.objects.create(**validated_data)
    


class StaffNotifyCallSerializer(serializers.ModelSerializer):


    requested_by = serializers.CharField()
    
    class Meta:
        model = NotifyCallRequest
        fields= ('id','requested_by', 'messeage' , 'requested_at' , 'seen')


class StaffofCourseDetailsSerializer(serializers.ModelSerializer):

    user = serializers.CharField()
    assigned_by = serializers.CharField()
    # course=serializers.CharField()
    course = CourseSerializer(read_only=True)

    

    class Meta:
        model= CourseEnrollment
        fields=('id', 'user' , 'assigned_by', 'course')


class StudentListbytaffDetailsSerializer(serializers.ModelSerializer):

    user = serializers.CharField()

    # course = CourseSerializer(read_only=True)
  

    class Meta:
        model= CourseEnrollment
        fields=('id', 'user' )



class CourseandStafAassignedDetailsSerializer(serializers.ModelSerializer):

    assigned_by = serializers.CharField()
    course = serializers.CharField()

    
    class Meta:
        model= CourseEnrollment
        fields=('id', 'course' , 'assigned_by')




