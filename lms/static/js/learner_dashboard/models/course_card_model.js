/**
 * Model for Course Programs.
 */
(function(define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'gettext',
        'jquery',
        'edx-ui-toolkit/js/utils/date-utils',
        'edx-ui-toolkit/js/utils/string-utils'
    ],
        function(Backbone, _, gettext, $, DateUtils, StringUtils) {
            return Backbone.Model.extend({
                initialize: function(data) {
                    if (data) {
                        this.context = data;
                        this.setActiveCourseRun(this.getCourseRun(data), data.user_preferences);
                    }
                },

                getCourseRun: function(course) {
                    var enrolledCourseRun = _.findWhere(course.course_runs, {is_enrolled: true}),
                        openEnrollmentCourseRuns = this.getEnrollableCourseRuns(),
                        desiredCourseRun;

                    // If the learner has an existing, unexpired enrollment,
                    // use it to populate the model.
                    if (enrolledCourseRun && !course.expired) {
                        desiredCourseRun = enrolledCourseRun;
                    } else if (openEnrollmentCourseRuns.length > 0) {
                        if (openEnrollmentCourseRuns.length === 1) {
                            desiredCourseRun = openEnrollmentCourseRuns[0];
                        } else {
                            desiredCourseRun = this.getUnselectedCourseRun(openEnrollmentCourseRuns);
                        }
                    } else {
                        desiredCourseRun = this.getUnselectedCourseRun(course.course_runs);
                    }

                    return desiredCourseRun;
                },

                isEnrolledInSession: function() {
                    // Returns true if the user is currently enrolled in a session of the course
                    return _.findWhere(this.context.course_runs, {is_enrolled: true}) !== undefined;
                },

                getUnselectedCourseRun: function(courseRuns) {
                    var unselectedRun = {},
                        courseRun;

                    if (courseRuns && courseRuns.length > 0) {
                        courseRun = courseRuns[0];

                        $.extend(unselectedRun, {
                            marketing_url: courseRun.marketing_url,
                            is_enrollment_open: courseRun.is_enrollment_open
                        });
                    }

                    return unselectedRun;
                },

                getEnrollableCourseRuns: function() {
                    var rawCourseRuns,
                        enrollableCourseRuns;

                    rawCourseRuns = _.where(this.context.course_runs, {
                        is_enrollment_open: true,
                        is_enrolled: false,
                        is_course_ended: false,
                        status: 'published'
                    });

                    // Deep copy to avoid mutating this.context.
                    enrollableCourseRuns = $.extend(true, [], rawCourseRuns);

                    // These are raw course runs from the server. The start
                    // dates are ISO-8601 formatted strings that need to be
                    // prepped for display.
                    _.each(enrollableCourseRuns, (function(courseRun) {
                        // eslint-disable-next-line no-param-reassign
                        courseRun.start_date = this.formatDate(courseRun.start);
                        // eslint-disable-next-line no-param-reassign
                        courseRun.end_date = this.formatDate(courseRun.end);

                        // This is used to render the date when selecting a course run to enroll in
                        // eslint-disable-next-line no-param-reassign
                        courseRun.dateString = this.formatDateString(courseRun);
                    }).bind(this));

                    return enrollableCourseRuns;
                },

                getUpcomingCourseRuns: function() {
                    return _.where(this.context.course_runs, {
                        is_enrollment_open: false,
                        is_enrolled: false,
                        is_course_ended: false,
                        status: 'published'
                    });
                },

                formatDate: function(date, userPreferences) {
                    var context,
                        userTimezone = '',
                        userLanguage = '';
                    if (userPreferences !== undefined) {
                        userTimezone = userPreferences.time_zone;
                        userLanguage = userPreferences['pref-lang'];
                    }
                    context = {
                        datetime: date,
                        timezone: userTimezone,
                        language: userLanguage,
                        format: DateUtils.dateFormatEnum.shortDate
                    };
                    return DateUtils.localize(context);
                },

                getCertificatePriceString: function(run) {
                    var upgradeableSeat, upgradeableSeats, currency;
                    if ('seats' in run && run.seats.length) {
                        // eslint-disable-next-line consistent-return
                        upgradeableSeats = _.filter(run.seats, function(seat) {
                            var upgradeableSeatTypes = ['verified', 'professional', 'no-id-professional', 'credit'];
                            if (upgradeableSeatTypes.indexOf(seat.type) >= 0) {
                                return seat;
                            }
                        });
                        if (upgradeableSeats.length > 0) {
                            upgradeableSeat = upgradeableSeats[0];
                            if (upgradeableSeat) {
                                currency = upgradeableSeat.currency;
                                if (currency === 'USD') {
                                    return '$' + upgradeableSeat.price;
                                } else {
                                    return upgradeableSeat.price + ' ' + currency;
                                }
                            }
                        }
                    }
                    return null;
                },

                formatDateString: function(run) {
                    var pacingType = run.pacing_type,
                        dateString,
                        start = this.valueIsDefined(run.start_date) ? run.advertised_start || run.start_date :
                            this.get('start_date'),
                        end = this.valueIsDefined(run.end_date) ? run.end_date : this.get('end_date'),
                        now = new Date(),
                        startDate = new Date(start),
                        endDate = new Date(end);

                    if (pacingType === 'self_paced') {
                        if (start) {
                            dateString = startDate > now ?
                                StringUtils.interpolate(gettext('(Self-paced) Starts {start}'), {start: start}) :
                                StringUtils.interpolate(gettext('(Self-paced) Started {start}'), {start: start});
                        } else if (end && endDate > now) {
                            dateString = StringUtils.interpolate(gettext('(Self-paced) Ends {end}'), {end: end});
                        } else if (end && endDate < now) {
                            dateString = StringUtils.interpolate(gettext('(Self-paced) Ended {end}'), {end: end});
                        }
                    } else {
                        if (start && end) {
                            dateString = start + ' - ' + end;
                        } else if (start) {
                            dateString = startDate > now ?
                                StringUtils.interpolate(gettext('Starts {start}'), {start: start}) :
                                StringUtils.interpolate(gettext('Started {start}'), {start: start});
                        } else if (end) {
                            dateString = StringUtils.interpolate(gettext('Ends {end}'), {end: end});
                        }
                    }
                    return dateString;
                },

                valueIsDefined: function(val) {
                    return !([undefined, 'None', null].indexOf(val) >= 0);
                },

                setActiveCourseRun: function(courseRun, userPreferences) {
                    var startDateString,
                        courseTitleLink = '',
                        isEnrolled = this.isEnrolledInSession() && courseRun.key;
                    if (courseRun) {
                        if (this.valueIsDefined(courseRun.advertised_start)) {
                            startDateString = courseRun.advertised_start;
                        } else {
                            startDateString = this.formatDate(courseRun.start, userPreferences);
                        }
                        if (isEnrolled && courseRun.course_url) {
                            courseTitleLink = courseRun.course_url;
                        } else if (!isEnrolled && courseRun.marketing_url) {
                            courseTitleLink = courseRun.marketing_url;
                        }
                        this.set({
                            certificate_url: courseRun.certificate_url,
                            course_run_key: courseRun.key || '',
                            course_url: courseRun.course_url || '',
                            title: this.context.title,
                            end_date: this.formatDate(courseRun.end, userPreferences),
                            enrollable_course_runs: this.getEnrollableCourseRuns(),
                            is_course_ended: courseRun.is_course_ended,
                            is_enrolled: isEnrolled,
                            is_enrollment_open: courseRun.is_enrollment_open,
                            course_key: this.context.key,
                            user_entitlement: this.context.user_entitlement,
                            is_unfulfilled_entitlement: this.context.user_entitlement && !isEnrolled,
                            marketing_url: courseRun.marketing_url,
                            mode_slug: courseRun.type,
                            start_date: startDateString,
                            upcoming_course_runs: this.getUpcomingCourseRuns(),
                            upgrade_url: courseRun.upgrade_url,
                            price: this.getCertificatePriceString(courseRun),
                            course_title_link: courseTitleLink
                        });

                        // This is used to render the date for completed and in progress courses
                        this.set({dateString: this.formatDateString(courseRun)});
                    }
                },

                setUnselected: function() {
                    // Called to reset the model back to the unselected state.
                    var unselectedCourseRun = this.getUnselectedCourseRun(this.get('enrollable_course_runs'));
                    this.setActiveCourseRun(unselectedCourseRun);
                },

                updateCourseRun: function(courseRunKey) {
                    var selectedCourseRun = _.findWhere(this.get('course_runs'), {key: courseRunKey});
                    if (selectedCourseRun) {
                        // Update the current context to set the course run to the enrolled state
                        _.each(this.context.course_runs, function(run) {
                            if (run.key === selectedCourseRun.key) run.is_enrolled = true; // eslint-disable-line no-param-reassign, max-len
                        });
                        this.setActiveCourseRun(selectedCourseRun);
                    }
                }
            });
        });
}).call(this, define || RequireJS.define);
