from django.db import models
import openedx.features.funix_relative_date.funix_relative_date as FunixRelativeDateModule


class LearnGoal(models.Model):
	user_id = models.CharField(max_length=255)
	course_id = models.CharField(max_length=255)
	hours_per_day = models.FloatField(default=2.5)
	weekday_0 = models.BooleanField(default=True)
	weekday_1 = models.BooleanField(default=True)
	weekday_2 = models.BooleanField(default=True)
	weekday_3 = models.BooleanField(default=True)
	weekday_4 = models.BooleanField(default=True)
	weekday_5 = models.BooleanField(default=False)
	weekday_6 = models.BooleanField(default=False)

	@classmethod
	def set_goal(self, course_id, user, hours_per_day, week_days):
		user_id = str(user.id)
		self.objects.filter(course_id=course_id, user_id=user_id).delete()

		goal_obj = LearnGoal(course_id=course_id, hours_per_day=hours_per_day, user_id=user_id)

		goal_obj.weekday_0 = week_days[0]
		goal_obj.weekday_1 = week_days[1]
		goal_obj.weekday_2 = week_days[2]
		goal_obj.weekday_3 = week_days[3]
		goal_obj.weekday_4 = week_days[4]
		goal_obj.weekday_5 = week_days[5]
		goal_obj.weekday_6 = week_days[6]

		goal_obj.save()

		return FunixRelativeDateModule.FunixRelativeDateLibary.get_schedule(user_name=str(user), course_id=str(course_id))

	@classmethod
	def get_goal(self, course_id, user_id):
		try:
			return self.objects.filter(course_id=course_id, user_id=user_id).get()
		except:
			return LearnGoal(course_id=course_id, user_id=user_id)
