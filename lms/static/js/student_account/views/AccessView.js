var edx = edx || {};

(function($, _, _s, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    // Bind to StateChange Event
    History.Adapter.bind( window, 'statechange', function() {
        /* Note: We are using History.getState() for legacy browser (IE) support
         * using History.js plugin instead of the native event.state
         */
        var State = History.getState();
    });

    edx.student.account.AccessView = Backbone.View.extend({
        el: '#login-and-registration-container',

        tpl: '#access-tpl',

        events: {
            'click .form-toggle': 'toggleForm'
        },

        subview: {
            login: {},
            register: {},
            passwordHelp: {}
        },

        urls: {
            dashboard: '/dashboard',
            payment: '/verify_student/start-flow/',
            trackSelection: '/course_modes/choose/'
        },

        // The form currently loaded
        activeForm: '',

        initialize: function( obj ) {
            /* Mix non-conflicting functions from underscore.string
             * (all but include, contains, and reverse) into the
             * Underscore namespace
             */
            _.mixin( _s.exports() );

            this.tpl = $(this.tpl).html();

            this.activeForm = obj.mode || 'login';

            this.thirdPartyAuth = obj.thirdPartyAuth || {
                currentProvider: null,
                providers: []
            };

            this.formDescriptions = {
                login: obj.loginFormDesc,
                register: obj.registrationFormDesc,
                reset: obj.passwordResetFormDesc
            };

            this.platformName = obj.platformName;

            // The login view listens for 'sync' events from the reset model
            this.resetModel = new edx.student.account.PasswordResetModel({}, {
                method: 'GET',
                url: '#'
            });

            this.render();
        },

        render: function() {
            $(this.el).html( _.template( this.tpl, {
                mode: this.activeForm
            }));

            this.postRender();

            return this;
        },

        postRender: function() {
            // Load the default form
            this.loadForm( this.activeForm );
        },

        loadForm: function( type ) {
            var loadFunc = _.bind( this.load[type], this );
            loadFunc( this.formDescriptions[type] );
        },

        load: {
            login: function( data ) {
                var model = new edx.student.account.LoginModel({}, {
                    method: data.method,
                    url: data.submit_url
                });

                this.subview.login =  new edx.student.account.LoginView({
                    fields: data.fields,
                    model: model,
                    resetModel: this.resetModel,
                    thirdPartyAuth: this.thirdPartyAuth,
                    platformName: this.platformName
                });

                // Listen for 'password-help' event to toggle sub-views
                this.listenTo( this.subview.login, 'password-help', this.resetPassword );

                // Listen for 'auth-complete' event so we can enroll/redirect the user appropriately.
                this.listenTo( this.subview.login, 'auth-complete', this.authComplete );

            },

            reset: function( data ) {
                this.resetModel.ajaxType = data.method;
                this.resetModel.urlRoot = data.submit_url;

                this.subview.passwordHelp = new edx.student.account.PasswordResetView({
                    fields: data.fields,
                    model: this.resetModel
                });

                // Listen for 'password-email-sent' event to toggle sub-views
                this.listenTo( this.subview.passwordHelp, 'password-email-sent', this.passwordEmailSent );

                // Focus on the form
                $('.password-reset-form').focus();
            },

            register: function( data ) {
                var model = new edx.student.account.RegisterModel({}, {
                    method: data.method,
                    url: data.submit_url
                });

                this.subview.register =  new edx.student.account.RegisterView({
                    fields: data.fields,
                    model: model,
                    thirdPartyAuth: this.thirdPartyAuth,
                    platformName: this.platformName
                });

                // Listen for 'auth-complete' event so we can enroll/redirect the user appropriately.
                this.listenTo( this.subview.register, 'auth-complete', this.authComplete );
            }
        },

        passwordEmailSent: function() {
            this.element.hide( $(this.el).find('#password-reset-anchor') );
            this.element.show( $('#login-anchor') );
            this.element.scrollTop( $('#login-anchor') );
        },

        resetPassword: function() {
            window.analytics.track('edx.bi.password_reset_form.viewed', {
                category: 'user-engagement'
            });

            this.element.hide( $(this.el).find('#login-anchor') );
            this.loadForm('reset');
            this.element.scrollTop( $('#password-reset-anchor') );
        },

        toggleForm: function( e ) {
            var type = $(e.currentTarget).data('type'),
                $form = $('#' + type + '-form'),
                $anchor = $('#' + type + '-anchor'),
                queryParams = url('?'),
                queryStr = queryParams.length > 0 ? '?' + queryParams : '';

            e.preventDefault();

            window.analytics.track('edx.bi.' + type + '_form.toggled', {
                category: 'user-engagement'
            });

            if ( !this.form.isLoaded( $form ) ) {
                this.loadForm( type );
            }

            this.element.hide( $(this.el).find('.submission-success') );
            this.element.hide( $(this.el).find('.form-wrapper') );
            this.element.show( $form );
            this.element.scrollTop( $anchor );

            // Update url without reloading page
            History.pushState( null, document.title, '/' + type + queryStr );
            analytics.page( 'login_and_registration', type );

            // Focus on the form
            document.getElementById(type).focus();
        },

        /**
         * Once authentication has completed successfully, a user may need to:
         *
         * - Enroll in a course.
         * - Update email opt-in preferences
         *
         * These actions are delegated from the authComplete function to additional
         * functions requiring authentication.
         *
         */
        authComplete: function() {
            var emailOptIn = edx.student.account.EmailOptInInterface,
                queryParams = this.queryParams();

            // Set the email opt in preference.
            if (!_.isUndefined(queryParams.emailOptIn) && queryParams.enrollmentAction) {
                emailOptIn.setPreference(
                    decodeURIComponent(queryParams.courseId),
                    queryParams.emailOptIn,
                    this
                ).always(this.enrollment);
            } else {
                this.enrollment();
            }
        },

        /**
         * Designed to be invoked after authentication has completed. This function enrolls
         * the student as requested.
         *
         * - Enroll in a course.
         * - Add a course to the shopping cart.
         * - Be redirected to the dashboard / track selection page / shopping cart.
         *
         * This handler is triggered upon successful authentication,
         * either from the login or registration form.  It checks
         * query string params, performs enrollment/shopping cart actions,
         * then redirects the user to the next page.
         *
         * The optional query string params are:
         *
         * ?next: If provided, redirect to this page upon successful auth.
         *   Django uses this when an unauthenticated user accesses a view
         *   decorated with @login_required.
         *
         * ?enrollment_action: Can be either "enroll" or "add_to_cart".
         *   If you provide this param, you must also provide a `course_id` param;
         *   otherwise, no action will be taken.
         *
         * ?course_id: The slash-separated course ID to enroll in or add to the cart.
         *
         */
        enrollment: function() {
            var enrollment = edx.student.account.EnrollmentInterface,
                shoppingcart = edx.student.account.ShoppingCartInterface,
                redirectUrl = this.urls.dashboard,
                queryParams = this.queryParams();

            if ( queryParams.enrollmentAction === 'enroll' && queryParams.courseId ) {
                var courseId = decodeURIComponent( queryParams.courseId );

                // Determine where to redirect the user after auto-enrollment.
                if ( !queryParams.courseMode ) {
                    /* Backwards compatibility with the original course details page.
                    The old implementation did not specify the course mode for enrollment,
                    so we'd always send the user to the "track selection" page.
                    The track selection page would allow the user to select the course mode
                    ("verified", "honor", etc.) -- or, if the only course mode was "honor",
                    it would redirect the user to the dashboard. */
                    redirectUrl = this.urls.trackSelection + courseId + '/';
                } else if ( queryParams.courseMode === 'honor' || queryParams.courseMode === 'audit' ) {
                    /* The newer version of the course details page allows the user
                    to specify which course mode to enroll as.  If the student has
                    chosen "honor", we send them immediately to the dashboard
                    rather than the payment flow.  The user may decide to upgrade
                    from the dashboard later. */
                    redirectUrl = this.urls.dashboard;
                } else {
                    /* If the user selected any other kind of course mode, send them
                    to the payment/verification flow. */
                    redirectUrl = this.urls.payment + courseId + '/';
                }

                /* Attempt to auto-enroll the user in a free mode of the course,
                then redirect to the next location. */
                enrollment.enroll( courseId, redirectUrl );
            } else if ( queryParams.enrollmentAction === 'add_to_cart' && queryParams.courseId) {
                /*
                If this is a paid course, add it to the shopping cart and redirect
                the user to the "view cart" page.
                */
                shoppingcart.addCourseToCart( decodeURIComponent( queryParams.courseId ) );
            } else {
                /*
                Otherwise, redirect the user to the next page
                Check for forwarding url and ensure that it isn't external.
                If not, use the default forwarding URL.
                */
                if ( !_.isNull( queryParams.next ) ) {
                    var next = decodeURIComponent( queryParams.next );

                    // Ensure that the URL is internal for security reasons
                    if ( !window.isExternal( next ) ) {
                        redirectUrl = next;
                    }
                }

                this.redirect( redirectUrl );
            }
        },

        /**
         * Redirect to a URL.  Mainly useful for mocking out in tests.
         * @param  {string} url The URL to redirect to.
         */
        redirect: function( url ) {
            window.location.href = url;
        },

        /**
         * Retrieve query params that we use post-authentication
         * to decide whether to enroll a student in a course, add
         * an item to the cart, or redirect.
         *
         * @return {object} The query params.  If any param is not
         * provided, it will default to null.
         */
        queryParams: function() {
            return {
                next: $.url( '?next' ),
                enrollmentAction: $.url( '?enrollment_action' ),
                courseId: $.url( '?course_id' ),
                courseMode: $.url( '?course_mode' ),
                emailOptIn: $.url( '?email_opt_in')
            };
        },

        form: {
            isLoaded: function( $form ) {
                return $form.html().length > 0;
            }
        },

        /* Helper method to toggle display
         * including accessibility considerations
         */
        element: {
            hide: function( $el ) {
                $el.addClass('hidden');
            },

            scrollTop: function( $el ) {
                // Scroll to top of selected element
                $('html,body').animate({
                    scrollTop: $el.offset().top
                },'slow');
            },

            show: function( $el ) {
                $el.removeClass('hidden');
            }
        }
    });
})(jQuery, _, _.str, Backbone, gettext);
