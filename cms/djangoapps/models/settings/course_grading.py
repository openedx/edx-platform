"""Grading policy"""


import json
import logging
from base64 import b64encode
from datetime import timedelta
from hashlib import sha1

from eventtracking import tracker

from cms.djangoapps.contentstore.signals.signals import GRADING_POLICY_CHANGED
from cms.djangoapps.models.settings.waffle import material_recompute_only
from common.djangoapps.track.event_transaction_utils import create_new_event_transaction_id
from xmodule.modulestore.django import modulestore  # lint-amnesty, pylint: disable=wrong-import-order

log = logging.getLogger(__name__)

GRADING_POLICY_CHANGED_EVENT_TYPE = 'edx.grades.grading_policy_changed'


class CourseGradingModel:
    """
    Basically a DAO and Model combo for CRUD operations pertaining to grading policy.
    """
    # Within this class, allow access to protected members of client classes.
    # This comes up when accessing kvs data and caches during kvs saves and modulestore writes.
    def __init__(self, course_descriptor):
        self.graders = [
            CourseGradingModel.jsonize_grader(i, grader) for i, grader in enumerate(course_descriptor.raw_grader)
        ]  # weights transformed to ints [0..100]
        self.grade_cutoffs = course_descriptor.grade_cutoffs
        self.grace_period = CourseGradingModel.convert_set_grace_period(course_descriptor)
        self.minimum_grade_credit = course_descriptor.minimum_grade_credit

    @classmethod
    def fetch(cls, course_key):
        """
        Fetch the course grading policy for the given course from persistence and return a CourseGradingModel.
        """
        descriptor = modulestore().get_course(course_key)
        model = cls(descriptor)
        return model

    @staticmethod
    def fetch_grader(course_key, index):
        """
        Fetch the course's nth grader
        Returns an empty dict if there's no such grader.
        """
        descriptor = modulestore().get_course(course_key)
        index = int(index)
        if len(descriptor.raw_grader) > index:
            return CourseGradingModel.jsonize_grader(index, descriptor.raw_grader[index])

        # return empty model
        else:
            return {"id": index,
                    "type": "",
                    "min_count": 0,
                    "drop_count": 0,
                    "short_label": None,
                    "weight": 0
                    }

    @staticmethod
    def update_from_json(course_key, jsondict, user):
        """
        Decode the json into CourseGradingModel and save any changes. Returns the modified model.
        Probably not the usual path for updates as it's too coarse grained.
        """
        descriptor = modulestore().get_course(course_key)
        previous_grading_policy_hash = str(hash_grading_policy(descriptor.grading_policy))

        graders_parsed = [CourseGradingModel.parse_grader(jsonele) for jsonele in jsondict['graders']]
        fire_signal = CourseGradingModel.must_fire_grading_event_and_signal(
            course_key,
            graders_parsed,
            descriptor,
            jsondict
        )
        descriptor.raw_grader = graders_parsed
        descriptor.grade_cutoffs = jsondict['grade_cutoffs']

        modulestore().update_item(descriptor, user.id)

        CourseGradingModel.update_grace_period_from_json(course_key, jsondict['grace_period'], user)

        CourseGradingModel.update_minimum_grade_credit_from_json(course_key, jsondict['minimum_grade_credit'], user)

        descriptor = modulestore().get_course(course_key)
        new_grading_policy_hash = str(hash_grading_policy(descriptor.grading_policy))
        log.info(
            "Updated course grading policy for course %s from %s to %s. fire_signal = %s",
            str(course_key),
            previous_grading_policy_hash,
            new_grading_policy_hash,
            fire_signal
        )

        if fire_signal:
            _grading_event_and_signal(course_key, user.id)

        return CourseGradingModel.fetch(course_key)

    @staticmethod
    def must_fire_grading_event_and_signal(course_key, proposed_grader_settings, course_from_modulestore, jsondict):
        """
        Detects if substantive enough changes were made to the proposed grader settings to warrant the firing of
        _grading_event_and_sngal
        Substantive changes mean the following values were changed:
            drop_count, weight, min_count
            An assignment type was added or removed
        """
        if course_from_modulestore.grade_cutoffs != jsondict['grade_cutoffs'] or \
                len(proposed_grader_settings) != len(course_from_modulestore.raw_grader):
            return True

        # because grading policy lists remain in the same order, we can do a single loop
        for i in range(len(course_from_modulestore.raw_grader)):
            if CourseGradingModel.must_fire_grading_event_and_signal_single_grader(
                course_key,
                proposed_grader_settings[i],
                course_from_modulestore.raw_grader[i]
            ):
                return True
        return False

    @staticmethod
    def must_fire_grading_event_and_signal_single_grader(
        course_key,
        proposed_grader_settings,
        existing_grader_settings
    ):
        """
        Detects changes in an individual grader vs an entire grading policy
         Detects if substantive enough changes were made to the proposed grader settings to warrant the firing of
        _grading_event_and_sngal
        Substantive changes mean the following values were changed:
            drop_count, weight, min_count
        """
        if not material_recompute_only(course_key):
            return True
        if existing_grader_settings['drop_count'] != proposed_grader_settings['drop_count'] or \
                existing_grader_settings['weight'] != proposed_grader_settings['weight'] or \
                existing_grader_settings['min_count'] != proposed_grader_settings['min_count']:
            return True
        return False

    @staticmethod
    def update_grader_from_json(course_key, grader, user):
        """
        Create or update the grader of the given type (string key) for the given course. Returns the modified
        grader which is a full model on the client but not on the server (just a dict)
        """
        descriptor = modulestore().get_course(course_key)
        previous_grading_policy_hash = str(hash_grading_policy(descriptor.grading_policy))

        # parse removes the id; so, grab it before parse
        index = int(grader.get('id', len(descriptor.raw_grader)))
        grader = CourseGradingModel.parse_grader(grader)

        fire_signal = True
        if index < len(descriptor.raw_grader):
            fire_signal = CourseGradingModel.must_fire_grading_event_and_signal_single_grader(
                course_key,
                grader,
                descriptor.raw_grader[index]
            )
            descriptor.raw_grader[index] = grader
        else:
            descriptor.raw_grader.append(grader)

        modulestore().update_item(descriptor, user.id)

        descriptor = modulestore().get_course(course_key)
        new_grading_policy_hash = str(hash_grading_policy(descriptor.grading_policy))
        log.info(
            "Updated grader for course %s. Grading policy has changed from %s to %s. fire_signal = %s",
            str(course_key),
            previous_grading_policy_hash,
            new_grading_policy_hash,
            fire_signal
        )
        if fire_signal:
            _grading_event_and_signal(course_key, user.id)

        return CourseGradingModel.jsonize_grader(index, descriptor.raw_grader[index])

    @staticmethod
    def update_cutoffs_from_json(course_key, cutoffs, user):
        """
        Create or update the grade cutoffs for the given course. Returns sent in cutoffs (ie., no extra
        db fetch).
        """
        descriptor = modulestore().get_course(course_key)
        descriptor.grade_cutoffs = cutoffs

        modulestore().update_item(descriptor, user.id)
        _grading_event_and_signal(course_key, user.id)
        return cutoffs

    @staticmethod
    def update_grace_period_from_json(course_key, graceperiodjson, user):
        """
        Update the course's default grace period. Incoming dict is {hours: h, minutes: m} possibly as a
        grace_period entry in an enclosing dict. It is also safe to call this method with a value of
        None for graceperiodjson.
        """
        descriptor = modulestore().get_course(course_key)

        # Before a graceperiod has ever been created, it will be None (once it has been
        # created, it cannot be set back to None).
        if graceperiodjson is not None:
            if 'grace_period' in graceperiodjson:
                graceperiodjson = graceperiodjson['grace_period']

            grace_timedelta = timedelta(**graceperiodjson)
            descriptor.graceperiod = grace_timedelta

            modulestore().update_item(descriptor, user.id)

    @staticmethod
    def update_minimum_grade_credit_from_json(course_key, minimum_grade_credit, user):
        """Update the course's default minimum grade requirement for credit.

        Args:
            course_key(CourseKey): The course identifier
            minimum_grade_json(Float): Minimum grade value
            user(User): The user object

        """
        descriptor = modulestore().get_course(course_key)

        # 'minimum_grade_credit' cannot be set to None
        if minimum_grade_credit is not None:
            minimum_grade_credit = minimum_grade_credit  # lint-amnesty, pylint: disable=self-assigning-variable

            descriptor.minimum_grade_credit = minimum_grade_credit
            modulestore().update_item(descriptor, user.id)

    @staticmethod
    def delete_grader(course_key, index, user):
        """
        Delete the grader of the given type from the given course.
        """
        descriptor = modulestore().get_course(course_key)

        index = int(index)
        if index < len(descriptor.raw_grader):
            del descriptor.raw_grader[index]
            # force propagation to definition
            descriptor.raw_grader = descriptor.raw_grader

        modulestore().update_item(descriptor, user.id)
        _grading_event_and_signal(course_key, user.id)

    @staticmethod
    def delete_grace_period(course_key, user):
        """
        Delete the course's grace period.
        """
        descriptor = modulestore().get_course(course_key)

        del descriptor.graceperiod

        modulestore().update_item(descriptor, user.id)

    @staticmethod
    def get_section_grader_type(location):
        descriptor = modulestore().get_item(location)
        return {
            "graderType": descriptor.format if descriptor.format is not None else 'notgraded',
            "location": str(location),
        }

    @staticmethod
    def update_section_grader_type(descriptor, grader_type, user):  # lint-amnesty, pylint: disable=missing-function-docstring
        if grader_type is not None and grader_type != 'notgraded':
            descriptor.format = grader_type
            descriptor.graded = True
        else:
            del descriptor.format
            del descriptor.graded

        modulestore().update_item(descriptor, user.id)
        _grading_event_and_signal(descriptor.location.course_key, user.id)
        return {'graderType': grader_type}

    @staticmethod
    def convert_set_grace_period(descriptor):  # lint-amnesty, pylint: disable=missing-function-docstring
        # 5 hours 59 minutes 59 seconds => converted to iso format
        rawgrace = descriptor.graceperiod
        if rawgrace:
            hours_from_days = rawgrace.days * 24
            seconds = rawgrace.seconds
            hours_from_seconds = int(seconds / 3600)
            hours = hours_from_days + hours_from_seconds
            seconds -= hours_from_seconds * 3600
            minutes = int(seconds / 60)
            seconds -= minutes * 60

            graceperiod = {'hours': 0, 'minutes': 0, 'seconds': 0}
            if hours > 0:
                graceperiod['hours'] = hours

            if minutes > 0:
                graceperiod['minutes'] = minutes

            if seconds > 0:
                graceperiod['seconds'] = seconds

            return graceperiod
        else:
            return None

    @staticmethod
    def parse_grader(json_grader):  # lint-amnesty, pylint: disable=missing-function-docstring
        # manual to clear out kruft
        result = {"type": json_grader["type"],
                  "min_count": int(json_grader.get('min_count', 0)),
                  "drop_count": int(json_grader.get('drop_count', 0)),
                  "short_label": json_grader.get('short_label', None),
                  "weight": float(json_grader.get('weight', 0)) / 100.0
                  }

        return result

    @staticmethod
    def jsonize_grader(i, grader):  # lint-amnesty, pylint: disable=missing-function-docstring
        # Warning: converting weight to integer might give unwanted results due
        # to the reason how floating point arithmetic works
        # e.g, "0.29 * 100 = 28.999999999999996"
        return {
            "id": i,
            "type": grader["type"],
            "min_count": grader.get('min_count', 0),
            "drop_count": grader.get('drop_count', 0),
            "short_label": grader.get('short_label', ""),
            "weight": grader.get('weight', 0) * 100,
        }


def _grading_event_and_signal(course_key, user_id):  # lint-amnesty, pylint: disable=missing-function-docstring
    name = GRADING_POLICY_CHANGED_EVENT_TYPE
    course = modulestore().get_course(course_key)
    grading_policy_hash = str(hash_grading_policy(course.grading_policy))
    data = {
        "course_id": str(course_key),
        "user_id": str(user_id),
        "grading_policy_hash": grading_policy_hash,
        "event_transaction_id": str(create_new_event_transaction_id()),
        "event_transaction_type": GRADING_POLICY_CHANGED_EVENT_TYPE,
    }
    tracker.emit(name, data)
    GRADING_POLICY_CHANGED.send(
        sender=CourseGradingModel,
        user_id=user_id,
        course_key=course_key,
        grading_policy_hash=grading_policy_hash
    )


def hash_grading_policy(grading_policy):  # lint-amnesty, pylint: disable=missing-function-docstring
    ordered_policy = json.dumps(
        grading_policy,
        separators=(',', ':'),  # Remove spaces from separators for more compact representation
        sort_keys=True,
    )
    return b64encode(sha1(ordered_policy.encode("utf-8")).digest()).decode('utf-8')
