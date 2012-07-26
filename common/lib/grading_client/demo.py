#!/usr/bin/env python

import numpy as np
from random import random
import datetime
from grading_client.api import *

# Create 30 local students, 100 remote students, 2 instructors, and 5 graders.

num_local, num_remote, num_instructors, num_graders = (30, 100, 2, 5)
local_students = [User(name="Student %d"%x, external_id="calx:%d"%(x+2000)).save() for x in xrange(num_local)]
remote_students = [User(name="Student %d"%x, external_id="edx:%d"%(x+1000)).save() for x in xrange(num_remote)]
instructors = [User(name="Instructor %d"%x, external_id="edx:%d"%x).save() for x in xrange(num_instructors)]
graders = [User(name="Grader %d"%x, external_id="edx:%d"%(x+100)).save() for x in xrange(num_graders)]

# Create 5 questions
num_questions = 5
questions = {}
group_names = ['local', 'remote1']
for variant in group_names:
  questions[variant] = [Question(external_id="calx_q:%d"%x, total_points=2, due_date=datetime.datetime.now()).save() for x in xrange(num_questions)]

# Submit submissions for all users
# Keep track of a "ground-truth" value for the scoring somehow
# Each question has 3 rubric items, worth 0, 1, and 1 (the 1s are independent of each other, the 0 is obviously not)

local_submissions = {}
# local_submissions_true_scores = np.ndarray((num_local, num_questions, 3), dtype=np.bool)
local_true_scores = {}
for question in questions['local']:
  local_submissions[question] = [(Submission(question_id=question.id, user_id=user.id, external_id="calx_s:%d"%(user.id+1000*question.id))) for user in local_students]
  for submission in local_submissions[question]:
    submission.save()
    m1 = (random() > 0.8)
    m2 = (random() > 0.7)
    correct = not (m1 or m2)
    local_true_scores[submission.id] = (m1, m2, correct)

# for user_index in xrange(num_local):
#   for question_index in xrange(num_questions):
#     # Randomly assign true evaluations
#     m1 = (random() > 0.8)
#     m2 = (random() > 0.7)
#     correct = not (m1 or m2)
#     local_submissions_true_scores[user_index][question_index] = (m1, m2, correct)


remote_submissions = {}
#remote_submissions_true_scores = np.ndarray((num_remote, num_questions, 3), dtype=np.bool)
for question in questions['remote1']:
  remote_submissions[question] = [Submission(question_id=question.id, user_id=user.id, external_id="edx_s:%d"%(user.id+1000*question.id)) for user in remote_students]
  for submission in remote_submissions[question]:
    submission.save()

# Instructor creates rubric

rubric = Rubric(rubric_type=1, title='My Rubric', total_points = 2).save()
rubric.add_entry(1, 'Mistake 1')
rubric.add_entry(2, 'Mistake 2')
rubric.add_entry(0, 'Perfect')
rubric.save() # Saves all the entries

# Instructor 1 evaluated some local submissions in the process of creating rubric
# This doesn't quite get the interleaving of rubric creation and evaluation, but
# it shouldn't matter in practice

inst1 = instructors[0]
instructor_evals = []
for question in questions['local']:
  for submission in local_submissions[question][:5]:
    entries_dict = { entry.id:value for entry, value in zip(rubric.entries, local_true_scores[submission.id]) }
    evaluation = rubric.create_evaluation(user_id=inst1.id, submission_id=submission.id, entry_values=entries_dict)
    #evaluation.save()
    instructor_evals.append(evaluation)

local_configurations = [question.grading_configuration for question in questions['local']]

# Create group for graders
grader_group = Group(title='Local Graders').save()
for user in graders:
  grader_group.add_user(user)

# Configure grading for readers
for config in local_configurations:
  config.evaluations_per_submission = 1
  config.evaluations_per_grader = num_local / num_graders
  config.training_exercises_required = 0
  config.open_date = datetime.datetime.now()
  config.due_date = datetime.datetime.now() # TODO FIX
  config.save()

  role = GroupRole(group_id=grader_group.id,grading_configuration_id=config.id,role=1)
  role.save()

# Now readers sign in and get work. Readers are also accurate in grading.
queue = question.grading_queue
for user in graders:
  for question, config in zip(questions['local'], local_configurations):
    tasks = queue.request_work_for_user(user)
    for task in tasks:
      submission = Submission.get_by_question_id_and_id(question.id, task.submission_id)    
      entries_dict = { entry.id:value for entry, value in zip(rubric.entries, local_true_scores[submission.id]) }
      evaluation = rubric.create_evaluation(user_id=user.id, submission_id=submission.id, entry_values=entries_dict)
      #evaluation.save()
