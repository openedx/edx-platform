/**
 * Model for Course Programs.
 */
(function(define) {
    'use strict';
    define([
        'backbone',
        'edx-ui-toolkit/js/utils/date-utils'
    ],
        function(Backbone, DateUtils) {
            return Backbone.Model.extend({
                initialize: function(data) {
                    if (data) {
                        this.context = data;
                        this.setActiveRunMode(this.getCourseRun(data.course_runs), data.user_preferences);
                    }
                },

                getUnselectedRunMode: function(course_runs) {
                    if (course_runs && course_runs.length > 0) {
                        return {
                            course_image_url: course_runs[0].course_image_url,
                            marketing_url: course_runs[0].marketing_url,
                            is_enrollment_open: course_runs[0].is_enrollment_open
                        };
                    }

                    return {};
                },

                getCourseRun: function(courseRuns) {
                    var enrolled_mode = _.findWhere(courseRuns, {is_enrolled: true}),
                        openEnrollmentRunModes = this.getEnrollableRunModes(),
                        desiredRunMode;
                    // We populate our model by looking at the run modes.
                    if (enrolled_mode) {
                    // If the learner is already enrolled in a run mode, return that one.
                        desiredRunMode = enrolled_mode;
                    } else if (openEnrollmentRunModes.length > 0) {
                        if (openEnrollmentRunModes.length === 1) {
                            desiredRunMode = openEnrollmentRunModes[0];
                        } else {
                            desiredRunMode = this.getUnselectedRunMode(openEnrollmentRunModes);
                        }
                    } else {
                        desiredRunMode = this.getUnselectedRunMode(courseRuns);
                    }

                    return desiredRunMode;
                },

                getEnrollableRunModes: function() {
                    return _.where(this.context.course_runs, {
                        is_enrollment_open: true,
                        is_enrolled: false,
                        is_course_ended: false
                    });
                },

                getUpcomingRunModes: function() {
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

                setActiveRunMode: function(courseRun, userPreferences) {
                    var startDateString;
                    if (courseRun) {
                        if (courseRun.advertised_start !== undefined && courseRun.advertised_start !== 'None') {
                            startDateString = courseRun.advertised_start;
                        } else {
                            startDateString = this.formatDate(
                                courseRun.start_date,
                                userPreferences
                            );
                        }
                        this.set({
                            certificate_url: courseRun.certificate_url,
                            course_image_url: courseRun.course_image_url || '',
                            course_key: courseRun.course_key,
                            course_url: courseRun.course_url || '',
                            display_name: this.context.display_name,
                            end_date: this.formatDate(
                                courseRun.end_date,
                                userPreferences
                            ),
                            enrollable_run_modes: this.getEnrollableRunModes(),
                            is_course_ended: courseRun.is_course_ended,
                            is_enrolled: courseRun.is_enrolled,
                            is_enrollment_open: courseRun.is_enrollment_open,
                            key: this.context.key,
                            marketing_url: courseRun.marketing_url,
                            mode_slug: courseRun.mode_slug,
                            run_key: courseRun.run_key,
                            start_date: startDateString,
                            upcoming_run_modes: this.getUpcomingRunModes(),
                            upgrade_url: courseRun.upgrade_url
                        });
                    }
                },
                setUnselected: function() {
                // Called to reset the model back to the unselected state.
                    var unselectedMode = this.getUnselectedRunMode(this.get('enrollable_run_modes'));
                    this.setActiveRunMode(unselectedMode);
                },

                updateRun: function(runKey) {
                    var selectedRun = _.findWhere(this.get('course_runs'), {run_key: runKey});
                    if (selectedRun) {
                        this.setActiveRunMode(selectedRun);
                    }
                }
            });
        });
}).call(this, define || RequireJS.define);
