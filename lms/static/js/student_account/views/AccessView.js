var edx = edx || {};

(function($, _, _s, Backbone, History) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.AccessView = Backbone.View.extend({
        el: '#login-and-registration-container',

        tpl: '#access-tpl',

        events: {
            'click .form-toggle': 'toggleForm'
        },

        subview: {
            login: {},
            register: {},
            passwordHelp: {},
            institutionLogin: {},
            hintedLogin: {}
        },

        nextUrl: '/dashboard',

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

            this.thirdPartyAuthHint = obj.thirdPartyAuthHint || null;

            if (obj.nextUrl) {
                // Ensure that the next URL is internal for security reasons
                if ( ! window.isExternal( obj.nextUrl ) ) {
                    this.nextUrl = obj.nextUrl;
                }
            }

            this.formDescriptions = {
                login: obj.loginFormDesc,
                register: obj.registrationFormDesc,
                reset: obj.passwordResetFormDesc,
                institution_login: null,
                hinted_login: null
            };

            this.platformName = obj.platformName;

            // The login view listens for 'sync' events from the reset model
            this.resetModel = new edx.student.account.PasswordResetModel({}, {
                method: 'GET',
                url: '#'
            });

            this.render();

            // Once the third party error message has been shown once,
            // there is no need to show it again, if the user changes mode:
            this.thirdPartyAuth.errorMessage = null;
        },

        render: function() {
            $(this.el).html( _.template( this.tpl, {
                mode: this.activeForm
            }));

            this.postRender();

            return this;
        },

        postRender: function() {
            //get & check current url hash part & load form accordingly
            if (Backbone.history.getHash() === "forgot-password-modal") {
                this.resetPassword();
            } else {
                this.loadForm(this.activeForm);
            }
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
            },

            institution_login: function ( unused ) {
                this.subview.institutionLogin =  new edx.student.account.InstitutionLoginView({
                    thirdPartyAuth: this.thirdPartyAuth,
                    platformName: this.platformName,
                    mode: this.activeForm
                });

                this.subview.institutionLogin.render();
            },

            hinted_login: function ( unused ) {
                this.subview.hintedLogin =  new edx.student.account.HintedLoginView({
                    thirdPartyAuth: this.thirdPartyAuth,
                    hintedProvider: this.thirdPartyAuthHint,
                    platformName: this.platformName
                });

                this.subview.hintedLogin.render();
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

            // Load the form. Institution login is always refreshed since it changes based on the previous form.
            if ( !this.form.isLoaded( $form ) || type == "institution_login") {
                this.loadForm( type );
            }
            this.activeForm = type;

            this.element.hide( $(this.el).find('.submission-success') );
            this.element.hide( $(this.el).find('.form-wrapper') );
            this.element.show( $form );
            this.element.scrollTop( $anchor );

            // Update url without reloading page
            if (type != "institution_login") {
                History.pushState( null, document.title, '/' + type + queryStr );
            }
            analytics.page( 'login_and_registration', type );

            // Focus on the form
            $("#" + type).focus();
        },

        /**
         * Once authentication has completed successfully:
         *
         * If we're in a third party auth pipeline, we must complete the pipeline.
         * Otherwise, redirect to the specified next step.
         *
         */
        authComplete: function() {
            if (this.thirdPartyAuth && this.thirdPartyAuth.finishAuthUrl) {
                this.redirect(this.thirdPartyAuth.finishAuthUrl);
                // Note: the third party auth URL likely contains another redirect URL embedded inside
            } else {
                this.redirect(this.nextUrl);
            }
        },

        /**
         * Redirect to a URL.  Mainly useful for mocking out in tests.
         * @param  {string} url The URL to redirect to.
         */
        redirect: function( url ) {
            window.location.replace(url);
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
})(jQuery, _, _.str, Backbone, History);
