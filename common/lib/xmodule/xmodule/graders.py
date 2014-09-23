import abc
import inspect
import logging
import random
import sys

from collections import namedtuple

log = logging.getLogger("edx.courseware")

# This is a tuple for holding scores, either from problems or sections.
# Section either indicates the name of the problem or the name of the section
Score = namedtuple("Score", "earned possible graded section module_id due")


def aggregate_scores(scores, section_name="summary"):
    """
    scores: A list of Score objects
    returns: A tuple (all_total, graded_total).
        all_total: A Score representing the total score summed over all input scores
        graded_total: A Score representing the score summed over all graded input scores
    """
    total_correct_graded = sum(score.earned for score in scores if score.graded)
    total_possible_graded = sum(score.possible for score in scores if score.graded)

    total_correct = sum(score.earned for score in scores)
    total_possible = sum(score.possible for score in scores)

    # regardless of whether or not it is graded
    all_total = Score(
        total_correct,
        total_possible,
        False,
        section_name,
        None,
        None,
    )
    # selecting only graded things
    graded_total = Score(
        total_correct_graded,
        total_possible_graded,
        True,
        section_name,
        None,
        None,
    )

    return all_total, graded_total


def invalid_args(func, argdict):
    """
    Given a function and a dictionary of arguments, returns a set of arguments
    from argdict that aren't accepted by func
    """
    args, _, keywords, _ = inspect.getargspec(func)
    if keywords:
        return set()  # All accepted
    return set(argdict) - set(args)


def grader_from_conf(conf):
    """
    This creates a CourseGrader from a configuration (such as in course_settings.py).
    The conf can simply be an instance of CourseGrader, in which case no work is done.
    More commonly, the conf is a list of dictionaries. A WeightedSubsectionsGrader
    with AssignmentFormatGrader's or SingleSectionGrader's as subsections will be
    generated. Every dictionary should contain the parameters for making either a
    AssignmentFormatGrader or SingleSectionGrader, in addition to a 'weight' key.
    """
    if isinstance(conf, CourseGrader):
        return conf

    subgraders = []
    for subgraderconf in conf:
        subgraderconf = subgraderconf.copy()
        weight = subgraderconf.pop("weight", 0)
        # NOTE: 'name' used to exist in SingleSectionGrader. We are deprecating SingleSectionGrader
        # and converting everything into an AssignmentFormatGrader by adding 'min_count' and
        # 'drop_count'. AssignmentFormatGrader does not expect 'name', so if it appears
        # in bad_args, go ahead remove it (this causes no errors). Eventually, SingleSectionGrader
        # should be completely removed.
        name = 'name'
        try:
            if 'min_count' in subgraderconf:
                #This is an AssignmentFormatGrader
                subgrader_class = AssignmentFormatGrader
            elif name in subgraderconf:
                #This is an SingleSectionGrader
                subgrader_class = SingleSectionGrader
            else:
                raise ValueError("Configuration has no appropriate grader class.")

            bad_args = invalid_args(subgrader_class.__init__, subgraderconf)
            # See note above concerning 'name'.
            if bad_args.issuperset({name}):
                bad_args = bad_args - {name}
                del subgraderconf[name]
            if len(bad_args) > 0:
                log.warning("Invalid arguments for a subgrader: %s", bad_args)
                for key in bad_args:
                    del subgraderconf[key]

            subgrader = subgrader_class(**subgraderconf)
            subgraders.append((subgrader, subgrader.category, weight))

        except (TypeError, ValueError) as error:
            # Add info and re-raise
            msg = ("Unable to parse grader configuration:\n    " +
                   str(subgraderconf) +
                   "\n    Error was:\n    " + str(error))
            raise ValueError(msg), None, sys.exc_info()[2]

    return WeightedSubsectionsGrader(subgraders)


class CourseGrader(object):
    """
    A course grader takes the totaled scores for each graded section (that a student has
    started) in the course. From these scores, the grader calculates an overall percentage
    grade. The grader should also generate information about how that score was calculated,
    to be displayed in graphs or charts.

    A grader has one required method, grade(), which is passed a grade_sheet. The grade_sheet
    contains scores for all graded section that the student has started. If a student has
    a score of 0 for that section, it may be missing from the grade_sheet. The grade_sheet
    is keyed by section format. Each value is a list of Score namedtuples for each section
    that has the matching section format.

    The grader outputs a dictionary with the following keys:
    - percent: Contains a float value, which is the final percentage score for the student.
    - section_breakdown: This is a list of dictionaries which provide details on sections
    that were graded. These are used for display in a graph or chart. The format for a
    section_breakdown dictionary is explained below.
    - grade_breakdown: This is a list of dictionaries which provide details on the contributions
    of the final percentage grade. This is a higher level breakdown, for when the grade is constructed
    of a few very large sections (such as Homeworks, Labs, a Midterm, and a Final). The format for
    a grade_breakdown is explained below. This section is optional.

    A dictionary in the section_breakdown list has the following keys:
    percent: A float percentage for the section.
    label: A short string identifying the section. Preferably fixed-length. E.g. "HW  3".
    detail: A string explanation of the score. E.g. "Homework 1 - Ohms Law - 83% (5/6)"
    category: A string identifying the category. Items with the same category are grouped together
    in the display (for example, by color).
    prominent: A boolean value indicating that this section should be displayed as more prominent
    than other items.

    A dictionary in the grade_breakdown list has the following keys:
    percent: A float percentage in the breakdown. All percents should add up to the final percentage.
    detail: A string explanation of this breakdown. E.g. "Homework - 10% of a possible 15%"
    category: A string identifying the category. Items with the same category are grouped together
    in the display (for example, by color).


    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def grade(self, grade_sheet, generate_random_scores=False):
        '''Given a grade sheet, return a dict containing grading information'''
        raise NotImplementedError


class WeightedSubsectionsGrader(CourseGrader):
    """
    This grader takes a list of tuples containing (grader, category_name, weight) and computes
    a final grade by totalling the contribution of each sub grader and multiplying it by the
    given weight. For example, the sections may be

    [ (homeworkGrader, "Homework", 0.15), (labGrader, "Labs", 0.15), (midtermGrader, "Midterm", 0.30),
      (finalGrader, "Final", 0.40) ]

    All items in section_breakdown for each subgrader will be combined. A grade_breakdown will be
    composed using the score from each grader.

    Note that the sum of the weights is not taken into consideration. If the weights add up to
    a value > 1, the student may end up with a percent > 100%. This allows for sections that
    are extra credit.
    """
    def __init__(self, sections):
        self.sections = sections

    def grade(self, grade_sheet, generate_random_scores=False):
        total_percent = 0.0
        section_breakdown = []
        grade_breakdown = []

        for subgrader, category, weight in self.sections:
            subgrade_result = subgrader.grade(grade_sheet, generate_random_scores)

            weighted_percent = subgrade_result['percent'] * weight
            section_detail = u"{0} = {1:.2%} of a possible {2:.2%}".format(category, weighted_percent, weight)

            total_percent += weighted_percent
            section_breakdown += subgrade_result['section_breakdown']
            grade_breakdown.append({'percent': weighted_percent, 'detail': section_detail, 'category': category})

        return {'percent': total_percent,
                'section_breakdown': section_breakdown,
                'grade_breakdown': grade_breakdown}


class SingleSectionGrader(CourseGrader):
    """
    This grades a single section with the format 'type' and the name 'name'.

    If the name is not appropriate for the short short_label or category, they each may
    be specified individually.
    """
    def __init__(self, type, name, short_label=None, category=None):
        self.type = type
        self.name = name
        self.short_label = short_label or name
        self.category = category or name

    def grade(self, grade_sheet, generate_random_scores=False):
        found_score = None
        if self.type in grade_sheet:
            for score in grade_sheet[self.type]:
                if score.section == self.name:
                    found_score = score
                    break

        if found_score or generate_random_scores:
            if generate_random_scores:  	# for debugging!
                earned = random.randint(2, 15)
                possible = random.randint(earned, 15)
            else:   # We found the score
                earned = found_score.earned
                possible = found_score.possible

            percent = earned / float(possible)
            detail = u"{name} - {percent:.0%} ({earned:.3n}/{possible:.3n})".format(
                name=self.name,
                percent=percent,
                earned=float(earned),
                possible=float(possible)
            )

        else:
            percent = 0.0
            detail = u"{name} - 0% (?/?)".format(name=self.name)

        breakdown = [{'percent': percent, 'label': self.short_label,
                      'detail': detail, 'category': self.category, 'prominent': True}]

        return {'percent': percent,
                'section_breakdown': breakdown,
                #No grade_breakdown here
                }


class AssignmentFormatGrader(CourseGrader):
    """
    Grades all sections matching the format 'type' with an equal weight. A specified
    number of lowest scores can be dropped from the calculation. The minimum number of
    sections in this format must be specified (even if those sections haven't been
    written yet).

    min_count defines how many assignments are expected throughout the course. Placeholder
    scores (of 0) will be inserted if the number of matching sections in the course is < min_count.
    If there number of matching sections in the course is > min_count, min_count will be ignored.

    show_only_average is to suppress the display of each assignment in this grader and instead
    only show the total score of this grader in the breakdown.

    hide_average is to suppress the display of the total score in this grader and instead
    only show each assignment in this grader in the breakdown.

    If there is only a single assignment in this grader, then it acts like a SingleSectionGrader
    and returns only one entry for the grader.  Since the assignment and the total are the same,
    the total is returned but is not labeled as an average.

    category should be presentable to the user, but may not appear. When the grade breakdown is
    displayed, scores from the same category will be similar (for example, by color).

    section_type is a string that is the type of a singular section. For example, for Labs it
    would be "Lab". This defaults to be the same as category.

    short_label is similar to section_type, but shorter. For example, for Homework it would be
    "HW".

    starting_index is the first number that will appear. For example, starting_index=3 and
    min_count = 2 would produce the labels "Assignment 3", "Assignment 4"

    """
    def __init__(self, type, min_count, drop_count, category=None, section_type=None, short_label=None,
                 show_only_average=False, hide_average=False, starting_index=1):
        self.type = type
        self.min_count = min_count
        self.drop_count = drop_count
        self.category = category or self.type
        self.section_type = section_type or self.type
        self.short_label = short_label or self.type
        self.show_only_average = show_only_average
        self.starting_index = starting_index
        self.hide_average = hide_average

    def grade(self, grade_sheet, generate_random_scores=False):
        def total_with_drops(breakdown, drop_count):
            '''calculates total score for a section while dropping lowest scores'''
            #create an array of tuples with (index, mark), sorted by mark['percent'] descending
            sorted_breakdown = sorted(enumerate(breakdown), key=lambda x: -x[1]['percent'])
            # A list of the indices of the dropped scores
            dropped_indices = []
            if drop_count > 0:
                dropped_indices = [x[0] for x in sorted_breakdown[-drop_count:]]
            aggregate_score = 0
            for index, mark in enumerate(breakdown):
                if index not in dropped_indices:
                    aggregate_score += mark['percent']

            if len(breakdown) - drop_count > 0:
                aggregate_score /= len(breakdown) - drop_count

            return aggregate_score, dropped_indices

        #Figure the homework scores
        scores = grade_sheet.get(self.type, [])
        breakdown = []
        for i in range(max(self.min_count, len(scores))):
            if i < len(scores) or generate_random_scores:
                if generate_random_scores:  	# for debugging!
                    earned = random.randint(2, 15)
                    possible = random.randint(earned, 15)
                    section_name = "Generated"

                else:
                    earned = scores[i].earned
                    possible = scores[i].possible
                    section_name = scores[i].section

                percentage = earned / float(possible)
                summary_format = u"{section_type} {index} - {name} - {percent:.0%} ({earned:.3n}/{possible:.3n})"
                summary = summary_format.format(
                    index=i + self.starting_index,
                    section_type=self.section_type,
                    name=section_name,
                    percent=percentage,
                    earned=float(earned),
                    possible=float(possible)
                )
            else:
                percentage = 0
                summary = u"{section_type} {index} Unreleased - 0% (?/?)".format(
                    index=i + self.starting_index,
                    section_type=self.section_type
                )

            short_label = u"{short_label} {index:02d}".format(
                index=i + self.starting_index,
                short_label=self.short_label
            )

            breakdown.append({'percent': percentage, 'label': short_label,
                              'detail': summary, 'category': self.category})

        total_percent, dropped_indices = total_with_drops(breakdown, self.drop_count)

        for dropped_index in dropped_indices:
            breakdown[dropped_index]['mark'] = {'detail': u"The lowest {drop_count} {section_type} scores are dropped."
                                                .format(drop_count=self.drop_count, section_type=self.section_type)}

        if len(breakdown) == 1:
            # if there is only one entry in a section, suppress the existing individual entry and the average,
            # and just display a single entry for the section.  That way it acts automatically like a
            # SingleSectionGrader.
            total_detail = u"{section_type} = {percent:.0%}".format(
                percent=total_percent,
                section_type=self.section_type,
            )
            total_label = u"{short_label}".format(short_label=self.short_label)
            breakdown = [{'percent': total_percent, 'label': total_label,
                          'detail': total_detail, 'category': self.category, 'prominent': True}, ]
        else:
            total_detail = u"{section_type} Average = {percent:.0%}".format(
                percent=total_percent,
                section_type=self.section_type
            )
            total_label = u"{short_label} Avg".format(short_label=self.short_label)

            if self.show_only_average:
                breakdown = []

            if not self.hide_average:
                breakdown.append({'percent': total_percent, 'label': total_label,
                                  'detail': total_detail, 'category': self.category, 'prominent': True})

        return {'percent': total_percent,
                'section_breakdown': breakdown,
                #No grade_breakdown here
                }
