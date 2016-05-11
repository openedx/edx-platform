from datetime import timedelta
from xmodule.modulestore.django import modulestore

from courses.models import Course as FunCourse


class CourseGradingModel(object):
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

        fun_course = FunCourse.objects.filter(key=unicode(course_descriptor.id))[:]
        self.minimum_grade_verified_certificate = fun_course[0].certificate_passing_grade if fun_course else None

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

        graders_parsed = [CourseGradingModel.parse_grader(jsonele) for jsonele in jsondict['graders']]

        descriptor.raw_grader = graders_parsed
        descriptor.grade_cutoffs = jsondict['grade_cutoffs']

        modulestore().update_item(descriptor, user.id)

        CourseGradingModel.update_grace_period_from_json(course_key, jsondict['grace_period'], user)

        CourseGradingModel.update_minimum_grade_credit_from_json(course_key, jsondict['minimum_grade_credit'], user)

        CourseGradingModel.update_minimum_grade_verified_certificate_from_json(
            course_key, jsondict['minimum_grade_verified_certificate']
        )

        return CourseGradingModel.fetch(course_key)

    @staticmethod
    def update_grader_from_json(course_key, grader, user):
        """
        Create or update the grader of the given type (string key) for the given course. Returns the modified
        grader which is a full model on the client but not on the server (just a dict)
        """
        descriptor = modulestore().get_course(course_key)

        # parse removes the id; so, grab it before parse
        index = int(grader.get('id', len(descriptor.raw_grader)))
        grader = CourseGradingModel.parse_grader(grader)

        if index < len(descriptor.raw_grader):
            descriptor.raw_grader[index] = grader
        else:
            descriptor.raw_grader.append(grader)

        modulestore().update_item(descriptor, user.id)

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
            minimum_grade_credit = minimum_grade_credit

            descriptor.minimum_grade_credit = minimum_grade_credit
            modulestore().update_item(descriptor, user.id)

    @staticmethod
    def update_minimum_grade_verified_certificate_from_json(course_key, minimum_grade_verified_certificate):
        """Update the course's default minimum grade requirement for verified certificate.

        Args:
            course_key(CourseKey): The course identifier
            minimum_grade_json(Float): Minimum grade value. If None there will be no minimum grade.

        """
        try:
            grade = float(minimum_grade_verified_certificate)
        except TypeError:
            grade = None
        FunCourse.objects.filter(key=unicode(course_key)).update(
            certificate_passing_grade=grade
        )

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
            "location": unicode(location),
        }

    @staticmethod
    def update_section_grader_type(descriptor, grader_type, user):
        if grader_type is not None and grader_type != u'notgraded':
            descriptor.format = grader_type
            descriptor.graded = True
        else:
            del descriptor.format
            del descriptor.graded

        modulestore().update_item(descriptor, user.id)
        return {'graderType': grader_type}

    @staticmethod
    def convert_set_grace_period(descriptor):
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
    def parse_grader(json_grader):
        # manual to clear out kruft
        result = {"type": json_grader["type"],
                  "min_count": int(json_grader.get('min_count', 0)),
                  "drop_count": int(json_grader.get('drop_count', 0)),
                  "short_label": json_grader.get('short_label', None),
                  "weight": float(json_grader.get('weight', 0)) / 100.0
                  }

        return result

    @staticmethod
    def jsonize_grader(i, grader):
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
