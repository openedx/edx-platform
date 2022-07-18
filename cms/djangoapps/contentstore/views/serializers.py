from xml.dom import ValidationErr
from sympy import Max, Min
from rest_framework import serializers # To Import
from common.djangoapps.student.models import Badges, CoursePoints

class BadgeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Badges
        fields = ('id','badge_name', 'min_points', 'badge_image', 'active')

#     # def validate(self, data):
#     #     max_points = data.get('max_points')
#     #     min_points =  data.get('min_points')

#     #     if min_points == max_points or min_points > max_points:
#     #         raise ValidationErr({"success":False, "message":{'error':"Min value shouldn\'t equal or greater to max value. "}})
        
#     #     all_badges = Badges.objects.all()
        
#     #     if all_badges.exists():
#     #         min_badge = all_badges.aggregate(Min('min_points'))
#     #         max_badge = all_badges.aggregate(Max('max_points'))
            
#     #         if min_badge.min_points > min_points and max_points!=min_badge.min_points:
#     #             raise ValidationErr({"success":False, "message":{"error":f'Max Points should be {min_badge.min_points}'}})
#     #         elif max_badge.max_points < min_points and max_badge.max_points != min_points:
#     #             raise ValidationErr({"success":False, "message":{"error":f'Min Points should be {max_badge.max_points}'}})
#     #         elif all_badges.filter(min_points__gte=min_points,max_points__lt=min_points):
#     #             raise ValidationErr({"success":False, "message":{"error":f'Min Points should not be in between of some other value.'}})
#     #         elif all_badges.filter(min_points__gte=max_points,max_points__lt=max_points):
#     #             raise ValidationErr({"success":False, "message":{"error":f'Max Points should not be in between of some other value.'}})

#     #     return data

class CoursePointsSerializer(serializers.ModelSerializer):

    class Meta:
        model = CoursePoints
        fields = ('course', 'chapter', 'reward_coins')











            