var edx = edx || {};

(function($) {
    'use strict';

    edx.dashboard = edx.dashboard || {};
    edx.dashboard.donation = {};

    /**
     * View for making donations for a course.
     * @constructor
     * @param {Object} params
     * @param {Object} params.el - The container element.
     * @param {string} params.course - The ID of the course for the donation.
     */
    edx.dashboard.donation.DonationView = function(params) {
        /**
         * Dynamically configure a form, which the client can submit
         * to the payment processor.
         * @param {Object} form - The form to modify.
         * @param {string} method - The HTTP method used to submit the form.
         * @param {string} url - The URL where the form data will be submitted.
         * @param {Object} params - Form data, included as hidden inputs.
         */
        var configureForm = function(form, method, url, params) {
            $('input', form).remove();
            form.attr('action', url);
            form.attr('method', method);
            _.each(params, function(value, key) {
                $('<input>').attr({
                    type: 'hidden',
                    name: key,
                    value: value
                }).appendTo(form);
            });
        };

        /**
        * Fire an analytics event indicating that the user
        * is about to be sent to the external payment processor.
        *
        * @param {string} course - The course ID for the donation.
        */
        var firePaymentAnalyticsEvent = function(course) {
            analytics.track(
                'edx.bi.user.payment_processor.visited',
                {
                    category: 'donations',
                    label: course
                }
            );
        };

        /**
        * Add a donation to the user's cart.
        *
        * @param {string} amount - The amount of the donation (e.g. "23.45")
        * @param {string} course - The ID of the course.
        * @returns {Object} The promise from the AJAX call to the server,
        *     which resolves with a data object of the form
        *     { payment_url: <string>, payment_params: <Object> }
        */
        var addDonationToCart = function(amount, course) {
            return $.ajax({
                url: '/shoppingcart/donation/',
                type: 'POST',
                data: {
                    amount: amount,
                    course_id: course
                }
            });
        };

        var view = {
            /**
            * Initialize the view.
            *
            * @param {Object} params
            * @param {JQuery selector} params.el - The container element.
            * @param {string} params.course - The ID of the course for the donation.
            * @returns {DonationView}
            */
            initialize: function(params) {
                this.$el = params.el;
                this.course = params.course;
                _.bindAll(view,
                    'render', 'donate', 'startPayment',
                    'validate', 'startPayment',
                    'displayServerError', 'submitPaymentForm'
                );
                return this;
            },

            /**
            * Render the form for making a donation for a course.
            *
            * @returns {DonationView}
            */
            render: function() {
                var html = _.template($('#donation-tpl').html())({});
                this.$el.html(html);
                this.$amount = $('input[name="amount"]', this.$el);
                this.$submit = $('.action-donate', this.$el);
                this.$errorMsg = $('.donation-error-msg', this.$el);
                this.$paymentForm = $('.payment-form', this.$el);
                this.$submit.click(this.donate);
                return this;
            },

            /**
            * Handle a click event on the "donate" button.
            * This will contact the LMS server to add the donation
            * to the user's cart, then send the user to the
            * external payment processor.
            *
            * @param {Object} event - The click event.
            */
            donate: function(event) {
                // Prevent form submission
                if (event) {
                    event.preventDefault();
                }

                // Immediately disable the submit button to prevent duplicate submissions
                this.$submit.addClass('disabled');

                if (this.validate()) {
                    var amount = this.$amount.val();
                    addDonationToCart(amount, this.course)
                        .done(this.startPayment)
                        .fail(this.displayServerError);
                } else {
                    // If an error occurred, allow the user to resubmit
                    this.$submit.removeClass('disabled');
                }
            },

            /**
            * Send signed payment parameters to the external
            * payment processor.
            *
            * @param {Object} data - The signed payment data received from the LMS server.
            * @param {string} data.payment_url - The URL of the external payment processor.
            * @param {Object} data.payment_data - Parameters to send to the external payment processor.
            */
            startPayment: function(data) {
                configureForm(
                    this.$paymentForm,
                    'post',
                    data.payment_url,
                    data.payment_params
                );
                firePaymentAnalyticsEvent(this.course);
                this.submitPaymentForm(this.$paymentForm);
            },

            /**
            * Validate the donation amount and mark any validation errors.
            *
            * @returns {boolean} True iff the form is valid.
            */
            validate: function() {
                var amount = this.$amount.val();
                var isValid = this.validateAmount(amount);

                if (isValid) {
                    this.$amount.removeClass('validation-error');
                    this.$errorMsg.text('');
                } else {
                    this.$amount.addClass('validation-error');
                    this.$errorMsg.text(
                        gettext('Please enter a valid donation amount.')
                    );
                }

                return isValid;
            },


            /**
            * Validate that the given amount is a valid currency string.
            *
            * @param {string} amount
            * @returns {boolean} True iff the amount is valid.
            */
            validateAmount: function(amount) {
                var amountRegex = /^\d+.\d{2}$|^\d+$/i;
                if (!amountRegex.test(amount)) {
                    return false;
                }

                if (parseFloat(amount) < 0.01) {
                    return false;
                }

                return true;
            },

            /**
            * Display an error message when we receive an error from the LMS server.
            */
            displayServerError: function() {
                // Display the error message
                this.$errorMsg.text(gettext('Your donation could not be submitted.'));

                // Re-enable the submit button to allow the user to retry
                this.$submit.removeClass('disabled');
            },

            /**
            * Submit the payment from to the external payment processor.
            * This is a separate function so we can easily stub it out in tests.
            *
            * @param {Object} form - The dynamically constructed payment form.
            */
            submitPaymentForm: function(form) {
                form.submit();
            }
        };

        view.initialize(params);
        return view;
    };

    $(document).ready(function() {
        // There may be multiple donation forms on the page
        // (one for each newly enrolled course).
        // For each one, create a new donation view to handle
        // that form, and parameterize it based on the
        // "data-course" attribute (the course ID).
        $('.donate-container').each(function() {
            var $container = $(this);
            var course = $container.data('course');
            var view = new edx.dashboard.donation.DonationView({
                el: $container,
                course: course
            }).render();
        });
    });
}(jQuery));
