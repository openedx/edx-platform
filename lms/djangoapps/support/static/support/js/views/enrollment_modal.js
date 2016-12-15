;(function (define) {
    'use strict';

    define([
        'backbone',
        'underscore',
        'gettext',
        'text!support/templates/enrollment-modal.underscore'
    ], function (Backbone, _, gettext, modalTemplate) {
        var EnrollmentModal = Backbone.View.extend({
            events: {
                'click .enrollment-change-submit': 'submitEnrollmentChange',
                'click .enrollment-change-cancel': 'cancel'
            },

            initialize: function (options) {
                this.enrollment = options.enrollment;
                this.modes = options.modes;
                this.reasons = options.reasons;
                this.template = modalTemplate;
            },

            render: function () {
                this.$el.html(_.template(this.template, {
                    enrollment: this.enrollment,
                    modes: this.modes,
                    reasons: this.reasons,
                }));
                return this;
            },

            show: function () {
                this.$el.removeClass('is-hidden').addClass('is-shown');
                this.render();
            },

            hide: function () {
                this.$el.removeClass('is-shown').addClass('is-hidden');
                this.render();
            },

            showErrors: function (errorMessage) {
                this.$('.enrollment-change-errors').text(errorMessage).css('display', '');
            },

            submitEnrollmentChange: function (event) {
                var new_mode = this.$('.enrollment-new-mode').val(),
                    reason = this.$('.enrollment-reason').val() || this.$('.enrollment-reason-other').val();
                event.preventDefault();
                if (!reason) {
                    this.showErrors(gettext('Please specify a reason.'));
                }
                else {
                    this.enrollment.updateEnrollment(new_mode, reason).then(
                        // Success callback
                        _.bind(function () {
                            this.hide();
                        }, this),
                        // Error callback
                        _.bind(function () {
                            this.showErrors(gettext(
                                'Something went wrong changing this enrollment. Please try again.'
                            ));
                        }, this)
                    );
                }
            },

            cancel: function (event) {
                event.preventDefault();
                this.hide();
            }
        });
        return EnrollmentModal;
    });
}).call(this, define || RequireJS.define);
