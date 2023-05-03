(function(define) {
    'use strict';
    define([
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/string-utils',
        'js/student_account/views/FormView',
        'text!templates/student_account/form_success.underscore',
        'text!templates/student_account/form_status.underscore'
    ], function(
        $, _, gettext,
        HtmlUtils,
        StringUtils,
        FormView,
        formSuccessTpl,
        formStatusTpl
    ) {
        return FormView.extend({
            el: '#login-form',
            tpl: '#login-tpl',
            events: {
                'click .js-login': 'submitForm',
                'click .forgot-password': 'forgotPassword',
                'click .login-provider': 'thirdPartyAuth',
                'click .enterprise-login': 'enterpriseSlugLogin',
                'click .login-help': 'toggleLoginHelp'
            },
            formType: 'login',
            requiredStr: '',
            optionalStr: '',
            submitButton: '.js-login',
            formSuccessTpl: formSuccessTpl,
            formStatusTpl: formStatusTpl,
            authWarningJsHook: 'js-auth-warning',
            passwordResetSuccessJsHook: 'js-password-reset-success',
            defaultFormErrorsTitle: gettext('We couldn\'t sign you in.'),
            isEnterpriseEnable: false,

            preRender: function(data) {
                this.providers = data.thirdPartyAuth.providers || [];
                this.hasSecondaryProviders = (
                    data.thirdPartyAuth.secondaryProviders && data.thirdPartyAuth.secondaryProviders.length
                );
                this.currentProvider = data.thirdPartyAuth.currentProvider || '';
                this.syncLearnerProfileData = data.thirdPartyAuth.syncLearnerProfileData || false;
                this.errorMessage = data.thirdPartyAuth.errorMessage || '';
                this.platformName = data.platformName;
                this.resetModel = data.resetModel;
                this.accountRecoveryModel = data.accountRecoveryModel;
                this.supportURL = data.supportURL;
                this.passwordResetSupportUrl = data.passwordResetSupportUrl;
                this.createAccountOption = data.createAccountOption;
                this.accountActivationMessages = data.accountActivationMessages;
                this.accountRecoveryMessages = data.accountRecoveryMessages;
                this.hideAuthWarnings = data.hideAuthWarnings;
                this.pipelineUserDetails = data.pipelineUserDetails;
                this.enterpriseName = data.enterpriseName;
                this.enterpriseSlugLoginURL = data.enterpriseSlugLoginURL;
                this.isEnterpriseEnable = data.isEnterpriseEnable;
                this.is_require_third_party_auth_enabled = data.is_require_third_party_auth_enabled || false;

                this.listenTo(this.model, 'sync', this.saveSuccess);
                this.listenTo(this.resetModel, 'sync', this.resetEmail);
                this.listenTo(this.accountRecoveryModel, 'sync', this.resetEmail);
            },

            render: function(html) {
                var fields = html || '';

                HtmlUtils.setHtml(
                    $(this.el),
                    HtmlUtils.HTML(
                        _.template(this.tpl)({
                            // We pass the context object to the template so that
                            // we can perform variable interpolation using sprintf
                            HtmlUtils: HtmlUtils,
                            context: {
                                fields: fields,
                                currentProvider: this.currentProvider,
                                syncLearnerProfileData: this.syncLearnerProfileData,
                                providers: this.providers,
                                hasSecondaryProviders: this.hasSecondaryProviders,
                                platformName: this.platformName,
                                createAccountOption: this.createAccountOption,
                                pipelineUserDetails: this.pipelineUserDetails,
                                enterpriseName: this.enterpriseName,
                                is_require_third_party_auth_enabled: this.is_require_third_party_auth_enabled
                            }
                        })
                    )
                );
                this.postRender();

                return this;
            },

            postRender: function() {
                var formErrorsTitle;
                this.$container = $(this.el);
                this.$form = this.$container.find('form');
                this.$formFeedback = this.$container.find('.js-form-feedback');
                this.$submitButton = this.$container.find(this.submitButton);

                if (this.errorMessage) {
                    formErrorsTitle = _.sprintf(
                        gettext('An error occurred when signing you in to %s.'),
                        this.platformName
                    );
                    this.renderErrors(formErrorsTitle, [this.errorMessage]);
                } else if (this.currentProvider) {
                    /* If we're already authenticated with a third-party
                     * provider, try logging in. The easiest way to do this
                     * is to simply submit the form.
                     */
                    this.model.save();
                }

                // Display account activation success or error messages.
                this.renderAccountActivationMessages();
                this.renderAccountRecoveryMessages();
            },

            renderAccountActivationMessages: function() {
                _.each(this.accountActivationMessages, this.renderMessage, this);
            },

            renderAccountRecoveryMessages: function() {
                _.each(this.accountRecoveryMessages, this.renderMessage, this);
            },

            renderMessage: function(message) {
                this.renderFormFeedback(this.formStatusTpl, {
                    jsHook: message.tags,
                    message: HtmlUtils.HTML(message.message)
                });
            },

            forgotPassword: function(event) {
                event.preventDefault();

                this.trigger('password-help');
                this.clearPasswordResetSuccess();
            },

            toggleLoginHelp: function(event) {
                var $help;
                event.preventDefault();
                $help = $('#login-help');
                this.toggleHelp(event, $help);
            },

            enterpriseSlugLogin: function(event) {
                event.preventDefault();
                if (this.enterpriseSlugLoginURL) {
                    window.location.href = this.enterpriseSlugLoginURL;
                }
            },

            postFormSubmission: function() {
                this.clearPasswordResetSuccess();
            },

            resetEmail: function() {
                var email = $('#password-reset-email').val(),
                    successTitle = gettext('Check Your Email'),
                    successMessageHtml = HtmlUtils.interpolateHtml(
                        gettext('{paragraphStart}You entered {boldStart}{email}{boldEnd}. If this email address is associated with your {platform_name} account, we will send a message with password recovery instructions to this email address.{paragraphEnd}' + // eslint-disable-line max-len
                        '{paragraphStart}If you do not receive a password reset message after 1 minute, verify that you entered the correct email address, or check your spam folder.{paragraphEnd}' + // eslint-disable-line max-len
                        '{paragraphStart}If you need further assistance, {anchorStart}contact technical support{anchorEnd}.{paragraphEnd}'), { // eslint-disable-line max-len
                            boldStart: HtmlUtils.HTML('<b data-hj-suppress>'),
                            boldEnd: HtmlUtils.HTML('</b>'),
                            paragraphStart: HtmlUtils.HTML('<p>'),
                            paragraphEnd: HtmlUtils.HTML('</p>'),
                            email: email,
                            platform_name: this.platformName,
                            anchorStart: HtmlUtils.HTML(
                                StringUtils.interpolate(
                                    '<a href="{passwordResetSupportUrl}">', {
                                        passwordResetSupportUrl: this.passwordResetSupportUrl
                                    }
                                )
                            ),
                            anchorEnd: HtmlUtils.HTML('</a>')
                        }
                    );

                this.clearFormErrors();
                this.clearPasswordResetSuccess();

                this.renderFormFeedback(this.formSuccessTpl, {
                    jsHook: this.passwordResetSuccessJsHook,
                    title: successTitle,
                    messageHtml: successMessageHtml
                });
            },

            thirdPartyAuth: function(event) {
                var providerUrl = $(event.currentTarget).data('provider-url') || '';

                if (providerUrl) {
                    window.location.href = providerUrl;
                }
            },

            saveSuccess: function() {
                this.trigger('auth-complete');
                this.clearPasswordResetSuccess();
            },

            saveError: function(error) {
                var errorCode;
                var msg;
                if (error.status === 0) {
                    msg = gettext('An error has occurred. Check your Internet connection and try again.');
                } else if (error.status === 500) {
                    msg = gettext('An error has occurred. Try refreshing the page, or check your Internet connection.'); // eslint-disable-line max-len
                } else if (error.responseJSON !== undefined && error.responseJSON.error_code === 'inactive-user') {
                    msg = HtmlUtils.interpolateHtml(
                        gettext('In order to sign in, you need to activate your account.{line_break}{line_break}' +
                            'We just sent an activation link to {strong_start} {email} {strong_end}. If ' +
                            ' you do not receive an email, check your spam folders or ' +
                            ' {anchorStart}contact {platform_name} Support{anchorEnd}.'),
                        {
                            email: error.responseJSON.email,
                            platform_name: this.platform_name,
                            line_break: HtmlUtils.HTML('<br/>'),
                            strong_start: HtmlUtils.HTML('<strong>'),
                            strong_end: HtmlUtils.HTML('</strong>'),
                            anchorStart: HtmlUtils.HTML(
                                StringUtils.interpolate(
                                    '<a href="{SupportUrl}">', {
                                        SupportUrl: this.supportURL,
                                    }
                                )
                            ),
                            anchorEnd: HtmlUtils.HTML('</a>')
                        }
                    );
                } else if (error.responseJSON !== undefined) {
                    msg = error.responseJSON.value;
                    errorCode = error.responseJSON.error_code;
                } else {
                    msg = gettext('An unexpected error has occurred.');
                }

                this.errors = [
                    StringUtils.interpolate(
                        '<li>{msg}</li>', {
                            msg: msg
                        }
                    )
                ];
                this.clearPasswordResetSuccess();

                /* If the user successfully authenticated with a third-party provider, but they haven't
                 * linked the accounts, instruct the user on how to link the accounts.
                 */
                if (errorCode === 'third-party-auth-with-no-linked-account' && this.currentProvider) {
                    if (!this.hideAuthWarnings) {
                        this.clearFormErrors();
                        this.renderThirdPartyAuthWarning();
                    }
                } else {
                    this.renderErrors(this.defaultFormErrorsTitle, this.errors);
                }
                this.toggleDisableButton(false);
            },

            renderThirdPartyAuthWarning: function() {
                var message = _.sprintf(
                    gettext('You have successfully signed into %(currentProvider)s, but your %(currentProvider)s' +
                            ' account does not have a linked %(platformName)s account. To link your accounts,' +
                            ' sign in now using your %(platformName)s password.'),
                    {currentProvider: this.currentProvider, platformName: this.platformName}
                );

                this.clearAuthWarning();
                this.renderFormFeedback(this.formStatusTpl, {
                    jsHook: this.authWarningJsHook,
                    message: message
                });
            },

            clearPasswordResetSuccess: function() {
                var query = '.' + this.passwordResetSuccessJsHook;
                this.clearFormFeedbackItems(query);
            },

            clearAuthWarning: function() {
                var query = '.' + this.authWarningJsHook;
                this.clearFormFeedbackItems(query);
            }
        });
    });
}).call(this, define || RequireJS.define);
