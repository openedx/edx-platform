var edx = edx || {};

(function($, _, _s, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.AccessView = Backbone.View.extend({
        el: '#login-and-registration-container',

        tpl: '#access-tpl',

        events: {
            'change .form-toggle': 'toggleForm'
        },

        subview: {
            login: {},
            register: {},
            passwordHelp: {}
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
            this.platformName = obj.platformName;

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
            this.$header = $(this.el).find('.js-login-register-header');
        },

        loadForm: function( type ) {
            this.getFormData( type, this );
        },

        load: {
            login: function( data, context ) {
                var model = new edx.student.account.LoginModel({}, {
                    method: data.method,
                    url: data.submit_url
                });

                context.subview.login =  new edx.student.account.LoginView({
                    fields: data.fields,
                    model: model,
                    thirdPartyAuth: context.thirdPartyAuth,
                    platformName: context.platformName
                });

                // Listen for 'password-help' event to toggle sub-views
                context.listenTo( context.subview.login, 'password-help', context.resetPassword );

                // Listen for 'auth-complete' event so we can enroll/redirect the user appropriately.
                context.listenTo( context.subview.login, 'auth-complete', context.authComplete );

            },

            reset: function( data, context ) {
                var model = new edx.student.account.PasswordResetModel({}, {
                    method: data.method,
                    url: data.submit_url
                });

                context.subview.passwordHelp = new edx.student.account.PasswordResetView({
                    fields: data.fields,
                    model: model
                });
            },

            register: function( data, context ) {
                var model = new edx.student.account.RegisterModel({}, {
                    method: data.method,
                    url: data.submit_url
                });

                context.subview.register =  new edx.student.account.RegisterView({
                    fields: data.fields,
                    model: model,
                    thirdPartyAuth: context.thirdPartyAuth,
                    platformName: context.platformName
                });

                // Listen for 'auth-complete' event so we can enroll/redirect the user appropriately.
                context.listenTo( context.subview.register, 'auth-complete', context.authComplete );
            }
        },

        getFormData: function( type, context ) {
            var urls = {
                login: 'login_session',
                register: 'registration',
                reset: 'password_reset'
            };

            $.ajax({
                url: '/user_api/v1/account/' + urls[type] + '/',
                type: 'GET',
                dataType: 'json',
                context: this,
                success: function( data ) {
                    this.load[type]( data, context );
                },
                error: this.showFormError
            });
        },

        resetPassword: function() {
            window.analytics.track('edx.bi.password_reset_form.viewed', {
                category: 'user-engagement'
            });

            this.element.hide( this.$header );
            this.element.hide( $(this.el).find('.form-type') );
            this.loadForm('reset');
            this.element.scrollTop( $('#password-reset-wrapper') );
        },

        showFormError: function() {
            this.element.show( $('#form-load-fail') );
        },

        toggleForm: function( e ) {
            var type = $(e.currentTarget).val(),
                $form = $('#' + type + '-form'),
                $anchor = $('#' + type + '-anchor');

            window.analytics.track('edx.bi.' + type + '_form.toggled', {
                category: 'user-engagement'
            });

            if ( !this.form.isLoaded( $form ) ) {
                this.loadForm( type );
            }

            this.element.hide( $(this.el).find('.form-wrapper') );
            this.element.show( $form );
            this.element.scrollTop( $anchor );
        },

        /**
         * Once authentication has completed successfully, a user may need to:
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
        authComplete: function() {
            var enrollment = edx.student.account.EnrollmentInterface,
                shoppingcart = edx.student.account.ShoppingCartInterface,
                redirectUrl = '/dashboard',
                queryParams = this.queryParams();

            if ( queryParams.enrollmentAction === 'enroll' && queryParams.courseId) {
                /*
                If we need to enroll in a course, mark as enrolled.
                The enrollment interface will redirect the student once enrollment completes.
                */
                enrollment.enroll( decodeURIComponent( queryParams.courseId ) );
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
                courseId: $.url( '?course_id' )
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
                $el.addClass('hidden')
                   .attr('aria-hidden', true);
            },

            scrollTop: function( $el ) {
                // Scroll to top of selected element
                $('html,body').animate({
                    scrollTop: $el.offset().top
                },'slow');
            },

            show: function( $el ) {
                $el.removeClass('hidden')
                   .attr('aria-hidden', false);
            }
        }
    });
})(jQuery, _, _.str, Backbone, gettext);
