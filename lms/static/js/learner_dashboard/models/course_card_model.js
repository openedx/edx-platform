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
                        this.setActiveRunMode(this.getRunMode(data.run_modes), data.user_preferences);
                    }
                },

                getUnselectedRunMode: function(runModes) {
                    if (runModes && runModes.length > 0) {
                        return {
                            course_image_url: runModes[0].course_image_url,
                            marketing_url: runModes[0].marketing_url,
                            is_enrollment_open: runModes[0].is_enrollment_open
                        };
                    }

                    return {};
                },

                getRunMode: function(runModes) {
                    var enrolled_mode = _.findWhere(runModes, {is_enrolled: true}),
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
                        desiredRunMode = this.getUnselectedRunMode(runModes);
                    }

                    return desiredRunMode;
                },

                getEnrollableRunModes: function() {
                    return _.where(this.context.run_modes, {
                        is_enrollment_open: true,
                        is_enrolled: false,
                        is_course_ended: false
                    });
                },

                getUpcomingRunModes: function() {
                    return _.where(this.context.run_modes, {
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

                setActiveRunMode: function(runMode, userPreferences) {
                    var startDateString;
                    if (runMode) {
                        if (runMode.advertised_start !== undefined && runMode.advertised_start !== 'None') {
                            startDateString = runMode.advertised_start;
                        } else {
                            startDateString = this.formatDate(
                                runMode.start_date,
                                userPreferences
                            );
                        }
                        this.set({
                            certificate_url: runMode.certificate_url,
                            course_image_url: runMode.course_image_url || '',
                            course_key: runMode.course_key,
                            course_url: runMode.course_url || '',
                            display_name: this.context.display_name,
                            end_date: this.formatDate(
                                runMode.end_date,
                                userPreferences
                            ),
                            enrollable_run_modes: this.getEnrollableRunModes(),
                            is_course_ended: runMode.is_course_ended,
                            is_enrolled: runMode.is_enrolled,
                            is_enrollment_open: runMode.is_enrollment_open,
                            key: this.context.key,
                            marketing_url: runMode.marketing_url,
                            mode_slug: runMode.mode_slug,
                            run_key: runMode.run_key,
                            start_date: startDateString,
                            upcoming_run_modes: this.getUpcomingRunModes(),
                            upgrade_url: runMode.upgrade_url
                        });
                    }
                },
                setUnselected: function() {
                // Called to reset the model back to the unselected state.
                    var unselectedMode = this.getUnselectedRunMode(this.get('enrollable_run_modes'));
                    this.setActiveRunMode(unselectedMode);
                },

                updateRun: function(runKey) {
                    var selectedRun = _.findWhere(this.get('run_modes'), {run_key: runKey});
                    if (selectedRun) {
                        this.setActiveRunMode(selectedRun);
                    }
                }
            });
        });
}).call(this, define || RequireJS.define);
