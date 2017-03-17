/**
 * Model for Course Programs.
 */
(function(define) {
    'use strict';
    define([
        'backbone',
        'underscore',
        'jquery',
        'edx-ui-toolkit/js/utils/date-utils'
    ],
        function(Backbone, _, $, DateUtils) {
            return Backbone.Model.extend({
                initialize: function(data) {
                    if (data) {
                        this.context = data;
                        this.setActiveCourseRun(this.getCourseRun(data.course_runs), data.user_preferences);
                    }
                },

                getCourseRun: function(courseRuns) {
                    var enrolledCourseRun = _.findWhere(courseRuns, {is_enrolled: true}),
                        openEnrollmentCourseRuns = this.getEnrollableCourseRuns(),
                        desiredCourseRun;

                    // We populate our model by looking at the course runs.
                    if (enrolledCourseRun) {
                        // If the learner is already enrolled in a course run, return that one.
                        desiredCourseRun = enrolledCourseRun;
                    } else if (openEnrollmentCourseRuns.length > 0) {
                        if (openEnrollmentCourseRuns.length === 1) {
                            desiredCourseRun = openEnrollmentCourseRuns[0];
                        } else {
                            desiredCourseRun = this.getUnselectedCourseRun(openEnrollmentCourseRuns);
                        }
                    } else {
                        desiredCourseRun = this.getUnselectedCourseRun(courseRuns);
                    }

                    return desiredCourseRun;
                },

                getUnselectedCourseRun: function(courseRuns) {
                    var unselectedRun = {},
                        courseRun,
                        courseImageUrl;

                    if (courseRuns && courseRuns.length > 0) {
                        courseRun = courseRuns[0];

                        if (courseRun.hasOwnProperty('image')) {
                            courseImageUrl = courseRun.image.src;
                        } else {
                            // The course_image_url property is attached by setActiveCourseRun.
                            // If that hasn't been called, it won't be present yet.
                            courseImageUrl = courseRun.course_image_url;
                        }

                        $.extend(unselectedRun, {
                            course_image_url: courseImageUrl,
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
                        is_course_ended: false
                    });

                    // Deep copy to avoid mutating this.context.
                    enrollableCourseRuns = $.extend(true, [], rawCourseRuns);

                    // These are raw course runs from the server. The start
                    // dates are ISO-8601 formatted strings that need to be
                    // prepped for display.
                    _.each(enrollableCourseRuns, (function(courseRun) {
                        // eslint-disable-next-line no-param-reassign
                        courseRun.start_date = this.formatDate(courseRun.start);
                    }).bind(this));

                    return enrollableCourseRuns;
                },

                getUpcomingCourseRuns: function() {
                    return _.where(this.context.course_runs, {
                        is_enrollment_open: false,
                        is_enrolled: false,
                        is_course_ended: false
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

                setActiveCourseRun: function(courseRun, userPreferences) {
                    var startDateString,
                        courseImageUrl;

                    if (courseRun) {
                        if (courseRun.advertised_start !== undefined && courseRun.advertised_start !== 'None') {
                            startDateString = courseRun.advertised_start;
                        } else {
                            startDateString = this.formatDate(courseRun.start, userPreferences);
                        }

                        if (courseRun.hasOwnProperty('image')) {
                            courseImageUrl = courseRun.image.src;
                        } else {
                            courseImageUrl = courseRun.course_image_url;
                        }

                        this.set({
                            certificate_url: courseRun.certificate_url,
                            course_image_url: courseImageUrl || '',
                            course_run_key: courseRun.key,
                            course_url: courseRun.course_url || '',
                            title: this.context.title,
                            end_date: this.formatDate(courseRun.end, userPreferences),
                            enrollable_course_runs: this.getEnrollableCourseRuns(),
                            is_course_ended: courseRun.is_course_ended,
                            is_enrolled: courseRun.is_enrolled,
                            is_enrollment_open: courseRun.is_enrollment_open,
                            course_key: this.context.key,
                            marketing_url: courseRun.marketing_url,
                            mode_slug: courseRun.type,
                            start_date: startDateString,
                            upcoming_course_runs: this.getUpcomingCourseRuns(),
                            upgrade_url: courseRun.upgrade_url
                        });
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
                        this.setActiveCourseRun(selectedCourseRun);
                    }
                }
            });
        });
}).call(this, define || RequireJS.define);
