from django.contrib.auth.models import Group

class JoinUs(models.Model):
	"""
	Models a user-created study group.
	"""
	name = models.CharField()
	members = models.ForeignKey(User, db_index=True)
	invite_code = models.CharField()
	# todo probably we want to do this with role/access control instead
	leader = models.ForeignKey(User, db_index=True)
	JOINUS_GROUP_PREFIX = "joinus_"

	@classmethod
	def join_group(cls, user, gname):
		""" Adds user to the JoinUs Group with name gname. """
		gname = JOINUS_GROUP_PREFIX + gname
		group = Group.objects.get(name='gname')
		g.user_set.add(user)
		return

	# Invite codes are future TODO; not in scope for datajam
	@classmethod
	def process_invite_code(cls, code, user):
		# if invite_code is valid
		# add_user_to_group
		# else, return error
		pass

	@classmethod
	def remove_user_from_group(cls, user, gname):
		""" 
		Removes user from the JoinUs Group with name gname.
		If that user is the group leader, this also deletes the group.
		"""
		gname = JOINUS_GROUP_PREFIX + gname
		group = Group.objects.get(name='gname')
		g.user_set.remove(user)
		# TODO if user is group leader, delete group
		return

	def get_group_info(self, user):
		# lets a user see the code they have access to
		pass

	@classmethod
	def create_group(cls, user, gname):
		# creates a new group led by user with name
		# TODO check that name is valid, not taken, etc
		gname = JOINUS_GROUP_PREFIX + gname
		if Group.objects.filter(name=gname):
			# return an error
			pass
		group = Group(name=gname)
		group.save()
		return
