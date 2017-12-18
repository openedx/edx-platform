(function(define) {
    'use strict';
    define(['backbone',
        'jquery',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils'
    ],
        function(Backbone, $, gettext, HtmlUtils) {
            return Backbone.View.extend({
                el: '.js-entitlement-unenrollment-modal',
                closeButtonSelector: '.js-entitlement-unenrollment-modal .js-entitlement-unenrollment-modal-close-btn',
                headerTextSelector: '.js-entitlement-unenrollment-modal .js-entitlement-unenrollment-modal-header-text',
                errorTextSelector: '.js-entitlement-unenrollment-modal .js-entitlement-unenrollment-modal-error-text',
                submitButtonSelector: '.js-entitlement-unenrollment-modal .js-entitlement-unenrollment-modal-submit',
                triggerSelector: '.js-entitlement-action-unenroll',
                mainPageSelector: '#dashboard-main',
                genericErrorMsg: gettext('Your unenrollment request could not be processed. Please try again later.'),

                initialize: function(options) {
                    var view = this;
                    this.dashboardPath = options.dashboardPath;
                    this.signInPath = options.signInPath;

                    this.$submitButton = $(this.submitButtonSelector);
                    this.$headerText = $(this.headerTextSelector);
                    this.$errorText = $(this.errorTextSelector);

                    this.$submitButton.on('click', this.handleSubmit.bind(this));

                    $(this.triggerSelector).each(function() {
                        var $trigger = $(this);

                        $trigger.on('click', view.handleTrigger.bind(view));

                        if (window.accessible_modal) {
                            window.accessible_modal(
                                '#' + $trigger.attr('id'),
                                view.closeButtonSelector,
                                '#' + view.$el.attr('id'),
                                view.mainPageSelector
                            );
                        }
                    });
                },

                handleTrigger: function(event) {
                    var $trigger = $(event.target),
                        courseName = $trigger.data('courseName'),
                        courseNumber = $trigger.data('courseNumber'),
                        apiEndpoint = $trigger.data('entitlementApiEndpoint');

                    this.resetModal();
                    this.setHeaderText(courseName, courseNumber);
                    this.setSubmitData(apiEndpoint);
                    this.$el.css('position', 'fixed');
                },

                handleSubmit: function() {
                    var apiEndpoint = this.$submitButton.data('entitlementApiEndpoint');

                    if (apiEndpoint === undefined) {
                        this.setError(this.genericErrorMsg);
                        return;
                    }

                    this.$submitButton.prop('disabled', true);
                    $.ajax({
                        url: apiEndpoint,
                        method: 'DELETE',
                        complete: this.onComplete.bind(this)
                    });
                },

                resetModal: function() {
                    this.$submitButton.removeData();
                    this.$submitButton.prop('disabled', false);
                    this.$headerText.empty();
                    this.$errorText.removeClass('entitlement-unenrollment-modal-error-text-visible');
                    this.$errorText.empty();
                },

                setError: function(message) {
                    this.$submitButton.prop('disabled', true);
                    this.$errorText.empty();
                    HtmlUtils.setHtml(
                        this.$errorText,
                        message
                    );
                    this.$errorText.addClass('entitlement-unenrollment-modal-error-text-visible');
                },

                setHeaderText: function(courseName, courseNumber) {
                    this.$headerText.empty();
                    HtmlUtils.setHtml(
                        this.$headerText,
                        HtmlUtils.interpolateHtml(
                            gettext('Are you sure you want to unenroll from {courseName} ({courseNumber})? You will be refunded the amount you paid.'), // eslint-disable-line max-len
                            {
                                courseName: courseName,
                                courseNumber: courseNumber
                            }
                        )
                    );
                },

                setSubmitData: function(apiEndpoint) {
                    this.$submitButton.removeData();
                    this.$submitButton.data('entitlementApiEndpoint', apiEndpoint);
                },

                onComplete: function(xhr) {
                    var status = xhr.status,
                        message = xhr.responseJSON && xhr.responseJSON.detail;

                    if (status === 204) {
                        this.redirectTo(this.dashboardPath);
                    } else if (status === 401 && message === 'Authentication credentials were not provided.') {
                        this.redirectTo(this.signInPath + '?next=' + encodeURIComponent(this.dashboardPath));
                    } else {
                        this.setError(this.genericErrorMsg);
                    }
                },

                redirectTo: function(path) {
                    window.location.href = path;
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
