(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone', 'gettext', 'edx-ui-toolkit/js/utils/string-utils',
        'js/models/notification', 'js/views/notification'],
        function($, _, Backbone, gettext, StringUtils) {
            /* global NotificationModel, NotificationView */

            var VerifiedTrackSettingsNotificationView = Backbone.View.extend({

                render: function() {
                    // All rendering is done in validateSettings, which must be called with some additional information.
                    return this;
                },

                validateSettings: function(isCohorted, cohortCollection, enableCohortsCheckbox) {
                    if (this.model.get('enabled')) {
                        var verifiedCohortName = this.model.get('verified_cohort_name');
                        if (isCohorted) {
                            var verifiedCohortExists = false;
                            $.each(cohortCollection, function(_, cohort) {
                                if (cohort.get('assignment_type') === 'manual' &&
                                        cohort.get('name') === verifiedCohortName) {
                                    verifiedCohortExists = true;
                                    cohort.disableEditingName = true;
                                } else {
                                    cohort.disableEditingName = false;
                                }
                            }
                            );
                            if (verifiedCohortExists) {
                                this.showNotification({
                                    type: 'confirmation',
                                    title: StringUtils.interpolate(
                                        gettext("This course uses automatic cohorting for verified track learners. You cannot disable cohorts, and you cannot rename the manual cohort named '{verifiedCohortName}'. To change the configuration for verified track cohorts, contact your edX partner manager."),  // eslint-disable-line max-len
                                        {verifiedCohortName: verifiedCohortName}
                                    )
                                });
                            } else {
                                this.showNotification({
                                    type: 'error',
                                    title: StringUtils.interpolate(
                                        gettext("This course has automatic cohorting enabled for verified track learners, but the required cohort does not exist. You must create a manually-assigned cohort named '{verifiedCohortName}' for the feature to work."),  // eslint-disable-line max-len
                                        {verifiedCohortName: verifiedCohortName}
                                    )
                                });
                            }
                            enableCohortsCheckbox.prop('disabled', true);
                        } else {
                            this.showNotification({
                                type: 'error',
                                title: gettext('This course has automatic cohorting enabled for verified track learners, but cohorts are disabled. You must enable cohorts for the feature to work.')  // eslint-disable-line max-len
                            });
                            enableCohortsCheckbox.prop('disabled', false);
                        }
                    }
                },

                showNotification: function(options) {
                    if (this.notification) {
                        this.notification.remove();
                    }
                    this.notification = new NotificationView({
                        model: new NotificationModel(options)
                    });

                    // It's ugly to reach outside to the cohort-management div, but we want this notification
                    // message to always be visible (as opposed to using the transient notification area defined
                    // by cohorts.js).
                    $('.cohort-management').before(this.notification.$el);

                    this.notification.render();
                }
            });
            return VerifiedTrackSettingsNotificationView;
        });
}).call(this, define || RequireJS.define);
