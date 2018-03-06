(function(define) {
    'use strict';
    define([
        'jquery',
        'backbone',
        'js/student_account/MSAMigrationStatus',
        'jquery.url'
    ], function($, Backbone, MSAMigrationStatus) {
        return Backbone.Model.extend({
            defaults: {
                email: '',
                password: '',
                remember: false
            },

            ajaxType: '',
            urlRoot: '',
            msaMigrationEnabled: false,
            msa_migration_pipeline_status: null,
            msaDefaultPassword: 'msa_email_lookup',

            initialize: function(attributes, options) {
                this.ajaxType = options.method;
                this.urlRoot = options.url;
                this.msaMigrationEnabled = options.msaMigrationEnabled;
                this.msa_migration_pipeline_status = options.msa_migration_pipeline_status;
            },

            sync: function(method, model) {
                var headers = {'X-CSRFToken': $.cookie('csrftoken')},
                    data = {},
                    analytics,
                    courseId = $.url('?course_id'),
                    MSA_MIGRATION_PIPELINE_STATUS = 'msa_migration_pipeline_status',
                    msaAttributes = {};


                // If there is a course ID in the query string param,
                // send that to the server as well so it can be included
                // in analytics events.
                if (courseId) {
                    analytics = JSON.stringify({
                        enroll_course_id: decodeURIComponent(courseId)
                    });
                }

                // Include all form fields and analytics info in the data sent to the server
                $.extend(data, model.attributes, {analytics: analytics});

                if (this.msaMigrationEnabled) {
                    if (!data.hasOwnProperty(MSA_MIGRATION_PIPELINE_STATUS)) {
                        msaAttributes[MSA_MIGRATION_PIPELINE_STATUS] = (
                            this.msa_migration_pipeline_status || MSAMigrationStatus.EMAIL_LOOKUP
                        );
                    }
                    if (msaAttributes[MSA_MIGRATION_PIPELINE_STATUS] === (
                        MSAMigrationStatus.EMAIL_LOOKUP || !data.password)) {
                        msaAttributes.password = model.msaDefaultPassword;
                    }

                    $.extend(data, msaAttributes);
                    this.msa_migration_pipeline_status = data[MSA_MIGRATION_PIPELINE_STATUS];
                }
                $.ajax({
                    url: model.urlRoot,
                    type: model.ajaxType,
                    data: data,
                    headers: headers,
                    success: function(json) {
                        if (model.msaMigrationEnabled) {
                            if (json.hasOwnProperty('value')) {
                                data[MSA_MIGRATION_PIPELINE_STATUS] = json.value;
                                // eslint-disable-next-line no-param-reassign
                                model.msa_migration_pipeline_status = json.value;
                            }

                            if (data[MSA_MIGRATION_PIPELINE_STATUS] === MSAMigrationStatus.LOGIN_NOT_MIGRATED) {
                                if (data.password !== model.msaDefaultPassword) {
                                    data[MSA_MIGRATION_PIPELINE_STATUS] = '';
                                } else {
                                    data.password = '';
                                }
                            }
                        }
                        model.trigger('sync', data);
                    },
                    error: function(error) {
                        model.trigger('error', error);
                    }
                });
            }
        });
    });
}).call(this, define || RequireJS.define);
