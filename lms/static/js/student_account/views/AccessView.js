;(function (define) {
    'use strict';
    define([
            'jquery',
            'utility',
            'underscore',
            'underscore.string',
            'backbone',
            'js/student_account/models/LoginModel',
            'js/student_account/models/PasswordResetModel',
            'js/student_account/models/RegisterModel',
            'js/student_account/views/LoginView',
            'js/student_account/views/PasswordResetView',
            'js/student_account/views/RegisterView',
            'js/student_account/views/InstitutionLoginView',
            'js/student_account/views/HintedLoginView',
            'js/vendor/history'
        ],
        function($, utility, _, _s, Backbone, LoginModel, PasswordResetModel, RegisterModel, LoginView,
                 PasswordResetView, RegisterView, InstitutionLoginView, HintedLoginView) {

        return Backbone.View.extend({
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

            initialize: function( options ) {

                /* Mix non-conflicting functions from underscore.string
                 * (all but include, contains, and reverse) into the
                 * Underscore namespace
                 */
                _.mixin( _s.exports() );

                this.tpl = $(this.tpl).html();

                this.activeForm = options.initial_mode || 'login';

                this.thirdPartyAuth = options.third_party_auth || {
                    currentProvider: null,
                    providers: []
                };

                this.thirdPartyAuthHint = options.third_party_auth_hint || null;

                if (options.login_redirect_url) {
                    // Ensure that the next URL is internal for security reasons
                    if ( ! window.isExternal( options.login_redirect_url ) ) {
                        this.nextUrl = options.login_redirect_url;
                    }
                }

                this.formDescriptions = {
                    login: options.login_form_desc,
                    register: options.registration_form_desc,
                    reset: options.password_reset_form_desc,
                    institution_login: null,
                    hinted_login: null
                };

                this.platformName = options.platform_name;
                this.supportURL = options.support_link;

                // The login view listens for 'sync' events from the reset model
                this.resetModel = new PasswordResetModel({}, {
                    method: 'GET',
                    url: '#'
                });

                this.render();

                // Once the third party error message has been shown once,
                // there is no need to show it again, if the user changes mode:
                this.thirdPartyAuth.errorMessage = null;
            },

            render: function() {
                $(this.el).html( _.template(this.tpl)({
                    mode: this.activeForm
                }));

                this.postRender();

                return this;
            },

            postRender: function() {
                //get & check current url hash part & load form accordingly
                if (Backbone.history.getHash() === 'forgot-password-modal') {
                    this.resetPassword();
                }
                this.loadForm(this.activeForm);

            },

            loadForm: function( type ) {
                var loadFunc = _.bind( this.load[type], this );
                loadFunc( this.formDescriptions[type] );
            },

            load: {
                login: function( data ) {
                    var model = new LoginModel({}, {
                        method: data.method,
                        url: data.submit_url
                    });

                    this.subview.login =  new LoginView({
                        fields: data.fields,
                        model: model,
                        resetModel: this.resetModel,
                        thirdPartyAuth: this.thirdPartyAuth,
                        platformName: this.platformName,
                        supportURL: this.supportURL
                    });

                    // Listen for 'password-help' event to toggle sub-views
                    this.listenTo( this.subview.login, 'password-help', this.resetPassword );

                    // Listen for 'auth-complete' event so we can enroll/redirect the user appropriately.
                    this.listenTo( this.subview.login, 'auth-complete', this.authComplete );

                },

                reset: function( data ) {
                    this.resetModel.ajaxType = data.method;
                    this.resetModel.urlRoot = data.submit_url;

                    this.subview.passwordHelp = new PasswordResetView({
                        fields: data.fields,
                        model: this.resetModel
                    });

                    // Listen for 'password-email-sent' event to toggle sub-views
                    this.listenTo( this.subview.passwordHelp, 'password-email-sent', this.passwordEmailSent );

                    // Focus on the form
                    $('.password-reset-form').focus();
                },

                register: function( data ) {
                    var model = new RegisterModel({}, {
                        method: data.method,
                        url: data.submit_url
                    });

                    this.subview.register =  new RegisterView({
                        fields: data.fields,
                        model: model,
                        thirdPartyAuth: this.thirdPartyAuth,
                        platformName: this.platformName
                    });

                    // Listen for 'auth-complete' event so we can enroll/redirect the user appropriately.
                    this.listenTo( this.subview.register, 'auth-complete', this.authComplete );
                },

                institution_login: function ( unused ) {
                    this.subview.institutionLogin =  new InstitutionLoginView({
                        thirdPartyAuth: this.thirdPartyAuth,
                        platformName: this.platformName,
                        mode: this.activeForm
                    });

                    this.subview.institutionLogin.render();
                },

                hinted_login: function ( unused ) {
                    this.subview.hintedLogin =  new HintedLoginView({
                        thirdPartyAuth: this.thirdPartyAuth,
                        hintedProvider: this.thirdPartyAuthHint,
                        platformName: this.platformName
                    });

                    this.subview.hintedLogin.render();
                }
            },

            passwordEmailSent: function() {
                var $loginAnchorElement = $('#login-anchor');
                this.element.hide( $(this.el).find('#password-reset-anchor') );
                this.element.show( $loginAnchorElement );
                this.element.scrollTop( $loginAnchorElement );
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
                if ( !this.form.isLoaded( $form ) || type == 'institution_login') {
                    this.loadForm( type );
                }
                this.activeForm = type;

                this.element.hide( $(this.el).find('.submission-success') );
                this.element.hide( $(this.el).find('.form-wrapper') );
                this.element.show( $form );
                this.element.scrollTop( $anchor );

                // Update url without reloading page
                if (type != 'institution_login') {
                    History.pushState( null, document.title, '/' + type + queryStr );
                }
                analytics.page( 'login_and_registration', type );

                // Focus on the form
                $('#' + type).focus();
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
    });
}).call(this, define || RequireJS.define);
