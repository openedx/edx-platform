/**
 * Once authentication has completed successfully, we may need to:
 *
 * - Enroll in a course.
 * - Add a course to the shopping cart.
 * - Update email opt-in preferences
 *
 * These actions are implemented by this view.
 *
 * This view may be initialized with the following optional parameters:
 * - courseId: string ID of the course in which to auto-enroll the user
 * - enrollmentAction: Can be either "enroll" or "add_to_cart". If you provide
 *      this param, you must also provide a `course_id` param; otherwise, no
 *      action will be taken.
 * - courseMode: optional. The mode to enroll in, e.g. "honor"
 * - emailOptIn: "true" or "false". Whether or not the user has opted in to
 *      emails from the course's organization.
 * - nextUrl: Redirect to this URL upon completion of all tasks, if possible
 *      and safe to do so.
 *
 * One the actions have been completed, the user will be redirected to either:
 * - The track selection or payment page (if they've been enrolled in a course that needs this)
 * - The specified 'nextUrl' if safe, or
 * - The dashboard
 */
(function(define, undefined) {
    'use strict';
    define([
        'jquery',
        'underscore',
        'backbone',
        'gettext',
        'js/student_account/emailoptin',
        'js/student_account/enrollment',
        'js/student_account/shoppingcart'
    ], function($, _, Backbone, gettext, emailOptInInterface, enrollmentInterface, shoppingCartInterface) {
        var FinishAuthView = Backbone.View.extend({
            el: '#finish-auth-status',

            urls: {
                finishAuth: '/account/finish_auth',
                defaultNextUrl: '/dashboard',
                payment: '/verify_student/start-flow/',
                trackSelection: '/course_modes/choose/'
            },

            initialize: function(obj) {
                var queryParams = {
                    next: $.url('?next'),
                    enrollmentAction: $.url('?enrollment_action'),
                    courseId: $.url('?course_id'),
                    courseMode: $.url('?course_mode'),
                    emailOptIn: $.url('?email_opt_in'),
                    purchaseWorkflow: $.url('?purchase_workflow')
                };
                for (var key in queryParams) {
                    if (queryParams[key]) {
                        queryParams[key] = decodeURIComponent(queryParams[key]);
                    }
                }
                this.courseId = queryParams.courseId;
                this.enrollmentAction = queryParams.enrollmentAction;
                this.courseMode = queryParams.courseMode;
                this.emailOptIn = queryParams.emailOptIn;
                this.nextUrl = this.urls.defaultNextUrl;
                this.purchaseWorkflow = queryParams.purchaseWorkflow;
                if (queryParams.next) {
                    // Ensure that the next URL is internal for security reasons
                    if (! window.isExternal(queryParams.next)) {
                        this.nextUrl = queryParams.next;
                    }
                }
            },

            render: function() {
                try {
                    var next = _.bind(this.enrollment, this);
                    this.checkEmailOptIn(next);
                } catch (err) {
                    this.updateTaskDescription(gettext('Error') + ': ' + err.message);
                    this.redirect(this.nextUrl);
                }
            },

            updateTaskDescription: function(desc) {
                // We don't display any detailed status updates to the user
                // but we do log them to the console to help with debugging.
                console.log(desc);
            },

            appendPurchaseWorkflow: function(redirectUrl) {
                if (this.purchaseWorkflow) {
                    // Append the purchase_workflow parameter to indicate
                    // whether this is a bulk purchase or a single seat purchase
                    redirectUrl += '?purchase_workflow=' + this.purchaseWorkflow;
                }
                return redirectUrl;
            },

            /**
             * Step 1:
             * Update the user's email preferences and then proceed to the next step
             */
            checkEmailOptIn: function(next) {
                // Set the email opt in preference. this.emailOptIn is null or "true" or "false"
                if ((this.emailOptIn === 'true' || this.emailOptIn === 'false') && this.enrollmentAction) {
                    this.updateTaskDescription(gettext('Saving your email preference'));
                    emailOptInInterface
                        .setPreference(this.courseId, this.emailOptIn)
                        .always(next);
                } else {
                    next();
                }
            },

            /**
             * Step 2. Handle enrollment:
             * - Enroll in a course or add a course to the shopping cart.
             * - Be redirected to the dashboard / track selection page / shopping cart.
             */
            enrollment: function() {
                var redirectUrl = this.nextUrl;

                if (this.enrollmentAction === 'enroll' && this.courseId) {
                    this.updateTaskDescription(gettext('Enrolling you in the selected course'));
                    var courseId = decodeURIComponent(this.courseId);

                    // Determine where to redirect the user after auto-enrollment.
                    if (!this.courseMode) {
                        /* Backwards compatibility with the original course details page.
                        The old implementation did not specify the course mode for enrollment,
                        so we'd always send the user to the "track selection" page.
                        The track selection page would allow the user to select the course mode
                        ("verified", "honor", etc.) -- or, if the only course mode was "honor",
                        it would redirect the user to the dashboard. */
                        redirectUrl = this.appendPurchaseWorkflow(this.urls.trackSelection + courseId + '/');
                    } else if (this.courseMode === 'honor' || this.courseMode === 'audit') {
                        /* The newer version of the course details page allows the user
                        to specify which course mode to enroll as.  If the student has
                        chosen "honor", we send them immediately to the next URL
                        rather than the payment flow.  The user may decide to upgrade
                        from the dashboard later. */
                    } else {
                        /* If the user selected any other kind of course mode, send them
                        to the payment/verification flow. */
                        redirectUrl = this.appendPurchaseWorkflow(this.urls.payment + courseId + '/');
                    }

                    /* Attempt to auto-enroll the user in a free mode of the course,
                    then redirect to the next location. */
                    enrollmentInterface.enroll(courseId, redirectUrl);
                } else if (this.enrollmentAction === 'add_to_cart' && this.courseId) {
                    /*
                    If this is a paid course, add it to the shopping cart and redirect
                    the user to the "view cart" page.
                    */
                    this.updateTaskDescription(gettext('Adding the selected course to your cart'));
                    shoppingCartInterface.addCourseToCart(this.courseId);
                } else {
                    // Otherwise, redirect the user to the next page.
                    this.redirect(redirectUrl);
                }
            },

            /**
             * Redirect to a URL.  Mainly useful for mocking out in tests.
             * @param  {string} url The URL to redirect to.
             */
            redirect: function(url) {
                this.updateTaskDescription(gettext('Loading your courses'));
                window.location.replace(url);
            }
        });
        return FinishAuthView;
    });
}).call(this, define || RequireJS.define);
