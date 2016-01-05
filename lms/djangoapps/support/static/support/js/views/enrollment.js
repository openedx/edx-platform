;(function (define) {
    'use strict';

    define([
        'backbone',
        'underscore',
        'moment',
        'support/js/views/enrollment_modal',
        'support/js/collections/enrollment',
        'text!support/templates/enrollment.underscore'
    ], function (Backbone, _, moment, EnrollmentModal, EnrollmentCollection, enrollmentTemplate) {
        return Backbone.View.extend({

            ENROLLMENT_CHANGE_REASONS: {
                'Financial Assistance': gettext('Financial Assistance'),
                'Upset Learner': gettext('Upset Learner'),
                'Teaching Assistant': gettext('Teaching Assistant')
            },

            events: {
                'submit .enrollment-form': 'search',
                'click .change-enrollment-btn': 'changeEnrollment'
            },

            initialize: function (options) {
                var user = options.user;
                this.initialUser = user;
                this.enrollmentSupportUrl = options.enrollmentSupportUrl;
                this.enrollments = new EnrollmentCollection([], {
                    user: user,
                    baseUrl: options.enrollmentsUrl
                });
                this.enrollments.on('change', _.bind(this.render, this));
            },

            render: function () {
                var user = this.enrollments.user;
                this.$el.html(_.template(enrollmentTemplate, {
                    user: user,
                    enrollments: this.enrollments,
                    formatDate: function (date) {
                        if (!date) {
                            return 'N/A';
                        }
                        else {
                            return moment(date).format('MM/DD/YYYY (H:MM UTC)');
                        }
                    }
                }));

                this.checkInitialSearch();
                return this;
            },

            /*
             * Check if the URL has provided an initial search, and
             * perform that search if so.
             */
            checkInitialSearch: function () {
                if (this.initialUser) {
                    delete this.initialUser;
                    this.$('.enrollment-form').submit();
                }
            },

            /*
             * Return the user's search string.
             */
            getSearchString: function () {
                return this.$('#enrollment-query-input').val();
            },

            /*
             * Perform the search. Renders the view on success.
             */
            search: function (event) {
                event.preventDefault();
                this.enrollments.user = this.getSearchString();
                this.enrollments.fetch({
                    success: _.bind(function () {
                        this.render();
                    }, this)
                });
            },

            /*
             * Show a modal view allowing the user to change a
             * learner's enrollment.
             */
            changeEnrollment: function (event) {
                var button = $(event.currentTarget),
                    course_id = button.data('course_id'),
                    modes = button.data('modes').split(','),
                    enrollment = this.enrollments.findWhere({course_id: course_id});
                event.preventDefault();
                new EnrollmentModal({
                    el: this.$('.enrollment-modal-wrapper'),
                    enrollment: enrollment,
                    modes: modes,
                    reasons: this.ENROLLMENT_CHANGE_REASONS
                }).show();
            }
        });
    });
}).call(this, define || RequireJS.define);
