def Group(models.Model):
	"""
	Models a user-created study group.
	"""
	name = models.CharField()
	members = models.ForeignKey(User, db_index=True)
	invite_code = models.CharField()
	# todo probably we want to do this with role/access control instead
	leader = models.ForeignKey(User, db_index=True)

	def join_group(self, user):
		# adds user to group (self)
		pass

	@classmethod
	def process_invite_code(cls, code, user):
		# if invite_code is valid
		# add_user_to_group
		# else, return error
		pass

	def remove_user_from_group(self, user):
		# remove user from group (self)
		pass

	def get_group_info(self, user):
		# lets a user see the code they have access to
		pass

	@classmethod
	def create_group(cls, user, name):
		# creates a new group led by user with name
		pass
