#
# File:   psychometrics/psychoanalyze.py
#
# generate pyschometrics plots from PsychometricData

from __future__ import division

import datetime
import logging
import json
import math
import numpy as np
from opaque_keys.edx.locator import BlockUsageLocator
from scipy.optimize import curve_fit

from django.conf import settings
from django.db.models import Sum, Max
from psychometrics.models import PsychometricData
from courseware.models import StudentModule
from pytz import UTC

log = logging.getLogger("edx.psychometrics")

#db = "ocwtutor"        # for debugging
#db = "default"

db = getattr(settings, 'DATABASE_FOR_PSYCHOMETRICS', 'default')

#-----------------------------------------------------------------------------
# fit functions


def func_2pl(x, a, b):
    """
    2-parameter logistic function
    """
    D = 1.7
    edax = np.exp(D * a * (x - b))
    return edax / (1 + edax)

#-----------------------------------------------------------------------------
# statistics class


class StatVar(object):
    """
    Simple statistics on floating point numbers: avg, sdv, var, min, max
    """
    def __init__(self, unit=1):
        self.sum = 0
        self.sum2 = 0
        self.cnt = 0
        self.unit = unit
        self.min = None
        self.max = None

    def add(self, x):
        if x is None:
            return
        if self.min is None:
            self.min = x
        else:
            if x < self.min:
                self.min = x
        if self.max is None:
            self.max = x
        else:
            if x > self.max:
                self.max = x
        self.sum += x
        self.sum2 += x ** 2
        self.cnt += 1

    def avg(self):
        if self.cnt is None:
            return 0
        return self.sum / 1.0 / self.cnt / self.unit

    def var(self):
        if self.cnt is None:
            return 0
        return (self.sum2 / 1.0 / self.cnt / (self.unit ** 2)) - (self.avg() ** 2)

    def sdv(self):
        v = self.var()
        if v > 0:
            return math.sqrt(v)
        else:
            return 0

    def __str__(self):
        return 'cnt=%d, avg=%f, sdv=%f' % (self.cnt, self.avg(), self.sdv())

    def __add__(self, x):
        self.add(x)
        return self

#-----------------------------------------------------------------------------
# histogram generator


def make_histogram(ydata, bins=None):
    '''
    Generate histogram of ydata using bins provided, or by default bins
    from 0 to 100 by 10.  bins should be ordered in increasing order.

    returns dict with keys being bins, and values being counts.
    special: hist['bins'] = bins
    '''
    if bins is None:
        bins = range(0, 100, 10)

    nbins = len(bins)
    hist = dict(zip(bins, [0] * nbins))
    for y in ydata:
        for b in bins[::-1]:  # in reverse order
            if y > b:
                hist[b] += 1
                break
    # hist['bins'] = bins
    return hist

#-----------------------------------------------------------------------------


def problems_with_psychometric_data(course_id):
    '''
    Return dict of {problems (location urls): count} for which psychometric data is available.
    Does this for a given course_id.
    '''
    pmdset = PsychometricData.objects.using(db).filter(studentmodule__course_id=course_id)
    plist = [p['studentmodule__module_state_key'] for p in pmdset.values('studentmodule__module_state_key').distinct()]
    problems = dict(
        (
            p,
            pmdset.filter(
                studentmodule__module_state_key=BlockUsageLocator.from_string(p)
            ).count()
        ) for p in plist
    )

    return problems

#-----------------------------------------------------------------------------


def generate_plots_for_problem(problem):

    pmdset = PsychometricData.objects.using(db).filter(
        studentmodule__module_state_key=BlockUsageLocator.from_string(problem)
    )
    nstudents = pmdset.count()
    msg = ""
    plots = []

    if nstudents < 2:
        msg += "%s nstudents=%d --> skipping, too few" % (problem, nstudents)
        return msg, plots

    max_grade = pmdset[0].studentmodule.max_grade

    agdat = pmdset.aggregate(Sum('attempts'), Max('attempts'))
    max_attempts = agdat['attempts__max']
    total_attempts = agdat['attempts__sum']  # not used yet

    msg += "max attempts = %d" % max_attempts

    xdat = range(1, max_attempts + 1)
    dataset = {'xdat': xdat}

    # compute grade statistics
    grades = [pmd.studentmodule.grade for pmd in pmdset]
    gsv = StatVar()
    for g in grades:
        gsv += g
    msg += "<br><p><font color='blue'>Grade distribution: %s</font></p>" % gsv

    # generate grade histogram
    ghist = []

    axisopts = """{
        xaxes: [{
            axisLabel: 'Grade'
        }],
        yaxes: [{
            position: 'left',
            axisLabel: 'Count'
         }]
         }"""

    if gsv.max > max_grade:
        msg += "<br/><p><font color='red'>Something is wrong: max_grade=%s, but max(grades)=%s</font></p>" % (max_grade, gsv.max)
        max_grade = gsv.max

    if max_grade > 1:
        ghist = make_histogram(grades, np.linspace(0, max_grade, max_grade + 1))
        ghist_json = json.dumps(ghist.items())

        plot = {'title': "Grade histogram for %s" % problem,
                'id': 'histogram',
                'info': '',
                'data': "var dhist = %s;\n" % ghist_json,
                'cmd': '[ {data: dhist, bars: { show: true, align: "center" }} ], %s' % axisopts,
                }
        plots.append(plot)
    else:
        msg += "<br/>Not generating histogram: max_grade=%s" % max_grade

    # histogram of time differences between checks
    # Warning: this is inefficient - doesn't scale to large numbers of students
    dtset = []  # time differences in minutes
    dtsv = StatVar()
    for pmd in pmdset:
        try:
            checktimes = eval(pmd.checktimes)  # update log of attempt timestamps
        except:
            continue
        if len(checktimes) < 2:
            continue
        ct0 = checktimes[0]
        for ct in checktimes[1:]:
            dt = (ct - ct0).total_seconds() / 60.0
            if dt < 20:  # ignore if dt too long
                dtset.append(dt)
                dtsv += dt
            ct0 = ct
    if dtsv.cnt > 2:
        msg += "<br/><p><font color='brown'>Time differences between checks: %s</font></p>" % dtsv
        bins = np.linspace(0, 1.5 * dtsv.sdv(), 30)
        dbar = bins[1] - bins[0]
        thist = make_histogram(dtset, bins)
        thist_json = json.dumps(sorted(thist.items(), key=lambda(x): x[0]))

        axisopts = """{ xaxes: [{ axisLabel: 'Time (min)'}], yaxes: [{position: 'left',axisLabel: 'Count'}]}"""

        plot = {'title': "Histogram of time differences between checks",
                'id': 'thistogram',
                'info': '',
                'data': "var thist = %s;\n" % thist_json,
                'cmd': '[ {data: thist, bars: { show: true, align: "center", barWidth:%f }} ], %s' % (dbar, axisopts),
                }
        plots.append(plot)

    # one IRT plot curve for each grade received (TODO: this assumes integer grades)
    for grade in range(1, int(max_grade) + 1):
        yset = {}
        gset = pmdset.filter(studentmodule__grade=grade)
        ngset = gset.count()
        if ngset == 0:
            continue
        ydat = []
        ylast = 0
        for x in xdat:
            y = gset.filter(attempts=x).count() / ngset
            ydat.append(y + ylast)
            ylast = y + ylast
        yset['ydat'] = ydat

        if len(ydat) > 3:  # try to fit to logistic function if enough data points
            try:
                cfp = curve_fit(func_2pl, xdat, ydat, [1.0, max_attempts / 2.0])
                yset['fitparam'] = cfp
                yset['fitpts'] = func_2pl(np.array(xdat), *cfp[0])
                yset['fiterr'] = [yd - yf for (yd, yf) in zip(ydat, yset['fitpts'])]
                fitx = np.linspace(xdat[0], xdat[-1], 100)
                yset['fitx'] = fitx
                yset['fity'] = func_2pl(np.array(fitx), *cfp[0])
            except Exception as err:
                log.debug('Error in psychoanalyze curve fitting: %s', err)

        dataset['grade_%d' % grade] = yset

    axisopts = """{
        xaxes: [{
            axisLabel: 'Number of Attempts'
        }],
        yaxes: [{
            max:1.0,
            position: 'left',
            axisLabel: 'Probability of correctness'
         }]
         }"""

    # generate points for flot plot
    for grade in range(1, int(max_grade) + 1):
        jsdata = ""
        jsplots = []
        gkey = 'grade_%d' % grade
        if gkey in dataset:
            yset = dataset[gkey]
            jsdata += "var d%d = %s;\n" % (grade, json.dumps(zip(xdat, yset['ydat'])))
            jsplots.append('{ data: d%d, lines: { show: false }, points: { show: true}, color: "red" }' % grade)
            if 'fitpts' in yset:
                jsdata += 'var fit = %s;\n' % (json.dumps(zip(yset['fitx'], yset['fity'])))
                jsplots.append('{ data: fit,  lines: { show: true }, color: "blue" }')
                (a, b) = yset['fitparam'][0]
                irtinfo = "(2PL: D=1.7, a=%6.3f, b=%6.3f)" % (a, b)
            else:
                irtinfo = ""

            plots.append({'title': 'IRT Plot for grade=%s %s' % (grade, irtinfo),
                          'id': "irt%s" % grade,
                          'info': '',
                          'data': jsdata,
                          'cmd': '[%s], %s' % (','.join(jsplots), axisopts),
                          })

    #log.debug('plots = %s' % plots)
    return msg, plots

#-----------------------------------------------------------------------------


def make_psychometrics_data_update_handler(course_id, user, module_state_key):
    """
    Construct and return a procedure which may be called to update
    the PsychometricData instance for the given StudentModule instance.
    """
    sm, status = StudentModule.objects.get_or_create(
        course_id=course_id,
        student=user,
        module_state_key=module_state_key,
        defaults={'state': '{}', 'module_type': 'problem'},
    )

    try:
        pmd = PsychometricData.objects.using(db).get(studentmodule=sm)
    except PsychometricData.DoesNotExist:
        pmd = PsychometricData(studentmodule=sm)

    def psychometrics_data_update_handler(state):
        """
        This function may be called each time a problem is successfully checked
        (eg on save_problem_check events in capa_module).

        state = instance state (a nice, uniform way to interface - for more future psychometric feature extraction)
        """
        try:
            state = json.loads(sm.state)
            done = state['done']
        except:
            log.exception("Oops, failed to eval state for %s (state=%s)", sm, sm.state)
            return

        pmd.done = done
        try:
            pmd.attempts = state.get('attempts', 0)
        except:
            log.exception("no attempts for %s (state=%s)", sm, sm.state)

        try:
            checktimes = eval(pmd.checktimes)  # update log of attempt timestamps
        except:
            checktimes = []
        checktimes.append(datetime.datetime.now(UTC))
        pmd.checktimes = checktimes
        try:
            pmd.save()
        except:
            log.exception("Error in updating psychometrics data for %s", sm)

    return psychometrics_data_update_handler
