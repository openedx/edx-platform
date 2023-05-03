(function(define) {
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
        'js/student_account/models/AccountRecoveryModel',
        'js/student_account/views/LoginView',
        'js/student_account/views/PasswordResetView',
        'js/student_account/views/RegisterView',
        'js/student_account/views/InstitutionLoginView',
        'js/student_account/views/HintedLoginView',
        'edx-ui-toolkit/js/utils/html-utils',
        'js/student_account/multiple_enterprise',
        'js/vendor/history'
    ],
    function($, utility, _, _s, Backbone, LoginModel, PasswordResetModel, RegisterModel, AccountRecoveryModel,
        LoginView, PasswordResetView, RegisterView, InstitutionLoginView, HintedLoginView, HtmlUtils,
        multipleEnterpriseInterface) {
        return Backbone.View.extend({
            tpl: '#access-tpl',
            events: {
                'click .form-toggle': 'toggleForm'
            },
            subview: {
                login: {},
                register: {},
                passwordHelp: {},
                accountRecoveryHelp: {},
                institutionLogin: {},
                hintedLogin: {}
            },
            nextUrl: '/dashboard',
            // The form currently loaded
            activeForm: '',

            initialize: function(options) {
                /* Mix non-conflicting functions from underscore.string
                 * (all but include, contains, and reverse) into the
                 * Underscore namespace
                 */
                _.mixin(_s.exports());
                this.tpl = $(this.tpl).html();

                this.activeForm = options.initial_mode || 'login';

                this.thirdPartyAuth = options.third_party_auth || {
                    currentProvider: null,
                    providers: []
                };

                this.thirdPartyAuthHint = options.third_party_auth_hint || null;
                this.edxUserInfoCookieName = options.edx_user_info_cookie_name || 'edx-user-info';

                // Account activation messages
                this.accountActivationMessages = options.account_activation_messages || [];
                this.accountRecoveryMessages = options.account_recovery_messages || [];

                if (options.login_redirect_url) {
                    this.nextUrl = options.login_redirect_url;
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
                this.passwordResetSupportUrl = options.password_reset_support_link;
                this.createAccountOption = options.account_creation_allowed;
                this.hideAuthWarnings = options.hide_auth_warnings || false;
                this.pipelineUserDetails = options.third_party_auth.pipeline_user_details;
                this.enterpriseName = options.enterprise_name || '';
                this.enterpriseSlugLoginURL = options.enterprise_slug_login_url || '';
                this.isEnterpriseEnable = options.is_enterprise_enable || false;
                this.isAccountRecoveryFeatureEnabled = options.is_account_recovery_feature_enabled || false;
                this.is_require_third_party_auth_enabled = options.is_require_third_party_auth_enabled || false;
                this.enable_coppa_compliance = options.enable_coppa_compliance;

                // The login view listens for 'sync' events from the reset model
                this.resetModel = new PasswordResetModel({}, {
                    method: 'GET',
                    url: '#'
                });

                this.accountRecoveryModel = new AccountRecoveryModel({}, {
                    method: 'GET',
                    url: '#'
                });

                this.render();

                // Once the third party error message has been shown once,
                // there is no need to show it again, if the user changes mode:
                this.thirdPartyAuth.errorMessage = null;

                // Once the account activation/account recovery messages have been shown once,
                // there is no need to show it again, if the user changes mode:
                this.accountActivationMessages = [];
                this.accountRecoveryMessages = [];
            },

            render: function() {
                HtmlUtils.setHtml(
                    $(this.el),
                    HtmlUtils.HTML(
                        _.template(this.tpl)({
                            mode: this.activeForm
                        })
                    )
                )
                this.postRender();

                return this;
            },

            postRender: function() {
                // get & check current url hash part & load form accordingly
                if (Backbone.history.getHash() === 'forgot-password-modal') {
                    this.resetPassword();
                }
                this.loadForm(this.activeForm);
            },

            loadForm: function(type) {
                var loadFunc;
                if (type === 'reset') {
                    loadFunc = _.bind(this.load.login, this);
                    loadFunc(this.formDescriptions.login);
                }
                loadFunc = _.bind(this.load[type], this);
                loadFunc(this.formDescriptions[type]);
            },

            load: {
                login: function(data) {
                    var model = new LoginModel({}, {
                        method: data.method,
                        url: data.submit_url
                    });
                    var isTpaSaml = this.thirdPartyAuth && this.thirdPartyAuth.finishAuthUrl ?
                        this.thirdPartyAuth.finishAuthUrl.indexOf('tpa-saml') >= 0 : false;

                    this.subview.login = new LoginView({
                        fields: data.fields,
                        model: model,
                        resetModel: this.resetModel,
                        accountRecoveryModel: this.accountRecoveryModel,
                        thirdPartyAuth: this.thirdPartyAuth,
                        accountActivationMessages: this.accountActivationMessages,
                        accountRecoveryMessages: this.accountRecoveryMessages,
                        platformName: this.platformName,
                        supportURL: this.supportURL,
                        passwordResetSupportUrl: this.passwordResetSupportUrl,
                        createAccountOption: this.createAccountOption,
                        hideAuthWarnings: this.hideAuthWarnings,
                        pipelineUserDetails: this.pipelineUserDetails,
                        enterpriseName: this.enterpriseName,
                        enterpriseSlugLoginURL: this.enterpriseSlugLoginURL,
                        isEnterpriseEnable: this.isEnterpriseEnable,
                        is_require_third_party_auth_enabled: this.is_require_third_party_auth_enabled
                    });

                    // Listen for 'password-help' event to toggle sub-views
                    this.listenTo(this.subview.login, 'password-help', this.resetPassword);

                    // Listen for 'auth-complete' event so we can enroll/redirect the user appropriately.
                    if (this.isEnterpriseEnable == true && !isTpaSaml) {
                        this.listenTo(this.subview.login, 'auth-complete', this.loginComplete);
                    } else {
                        this.listenTo(this.subview.login, 'auth-complete', this.authComplete);
                    }
                },

                reset: function(data) {
                    this.resetModel.ajaxType = data.method;
                    this.resetModel.urlRoot = data.submit_url;

                    this.subview.passwordHelp = new PasswordResetView({
                        fields: data.fields,
                        model: this.resetModel
                    });

                    // Listen for 'password-email-sent' event to toggle sub-views
                    this.listenTo(this.subview.passwordHelp, 'password-email-sent', this.passwordEmailSent);

                    // Focus on the form
                    $('.password-reset-form').focus();
                },

                register: function(data) {
                    var model = new RegisterModel({}, {
                        method: data.method,
                        url: data.submit_url,
                        nextUrl: this.nextUrl
                    });

                    this.subview.register = new RegisterView({
                        fields: data.fields,
                        model: model,
                        thirdPartyAuth: this.thirdPartyAuth,
                        platformName: this.platformName,
                        hideAuthWarnings: this.hideAuthWarnings,
                        is_require_third_party_auth_enabled: this.is_require_third_party_auth_enabled,
                        enableCoppaCompliance: this.enable_coppa_compliance,
                    });

                    // Listen for 'auth-complete' event so we can enroll/redirect the user appropriately.
                    this.listenTo(this.subview.register, 'auth-complete', this.authComplete);
                },

                institution_login: function(unused) {
                    this.subview.institutionLogin = new InstitutionLoginView({
                        thirdPartyAuth: this.thirdPartyAuth,
                        platformName: this.platformName,
                        mode: this.activeForm
                    });

                    this.subview.institutionLogin.render();
                },

                hinted_login: function(unused) {
                    this.subview.hintedLogin = new HintedLoginView({
                        thirdPartyAuth: this.thirdPartyAuth,
                        hintedProvider: this.thirdPartyAuthHint,
                        platformName: this.platformName
                    });

                    this.subview.hintedLogin.render();
                }
            },

            passwordEmailSent: function() {
                var $loginAnchorElement = $('#login-form');
                this.element.hide($(this.el).find('#password-reset-anchor'));
                this.element.show($loginAnchorElement);
                this.element.scrollTop($loginAnchorElement);
            },

            resetPassword: function() {
                window.analytics.track('edx.bi.password_reset_form.viewed', {
                    category: 'user-engagement'
                });

                this.element.hide($(this.el).find('#login-form'));
                this.loadForm('reset');
                this.element.scrollTop($('#password-reset-anchor'));
            },

            toggleForm: function(e) {
                var type = $(e.currentTarget).data('type'),
                    $form = $('#' + type + '-form'),
                    scrollX = window.scrollX,
                    scrollY = window.scrollY,
                    queryParams = url('?'),
                    queryStr = queryParams.length > 0 ? '?' + queryParams : '';

                e.preventDefault();

                window.analytics.track('edx.bi.' + type + '_form.toggled', {
                    category: 'user-engagement'
                });

                // Load the form. Institution login is always refreshed since it changes based on the previous form.
                if (!this.form.isLoaded($form) || type == 'institution_login') {

                    // We need a special case for loading reset form as there is mismatch of form id
                    // value ie 'password-reset' vs load function name ie 'reset'
                    if (type === 'password-reset') {
                        type = 'reset';
                    }
                    this.loadForm(type);
                }
                this.activeForm = type;

                this.element.hide($(this.el).find('.submission-success'));
                this.element.hide($(this.el).find('.form-wrapper'));
                this.element.show($form);

                // Update url without reloading page
                if (type != 'institution_login' && type != 'reset') {
                    History.pushState(null, document.title, '/' + type + queryStr);
                }
                analytics.page('login_and_registration', type);

                // Focus on the form
                $('#' + type).focus();

                // Maintain original scroll position
                window.scrollTo(scrollX, scrollY);
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
            /**
             * Take a learner attached to multiple enterprises to the enterprise selection page:
             *
             */
            loginComplete: function() {
                if (this.thirdPartyAuth && this.thirdPartyAuth.finishAuthUrl) {
                    multipleEnterpriseInterface.check(
                        this.thirdPartyAuth.finishAuthUrl,
                        this.edxUserInfoCookieName
                    );
                    // Note: the third party auth URL likely contains another redirect URL embedded inside
                } else {
                    multipleEnterpriseInterface.check(this.nextUrl, this.edxUserInfoCookieName);
                }
            },

            /**
             * Redirect to a URL.  Mainly useful for mocking out in tests.
             * @param  {string} url The URL to redirect to.
             */
            redirect: function(url) {
                window.location.replace(url);
            },

            form: {
                isLoaded: function($form) {
                    return $form.html().length > 0;
                }
            },

            /* Helper method to toggle display
             * including accessibility considerations
             */
            element: {
                hide: function($el) {
                    $el.addClass('hidden');
                },

                scrollTop: function($el) {
                    // Scroll to top of selected element
                    $('html,body').animate({
                        scrollTop: $el.offset().top
                    }, 'slow');
                },

                show: function($el) {
                    $el.removeClass('hidden');
                }
            }
        });
    });
}).call(this, define || RequireJS.define);
