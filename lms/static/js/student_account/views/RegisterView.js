(function(define) {
    'use strict';
    define([
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'js/student_account/views/FormView',
        'text!templates/student_account/form_status.underscore'
    ],
        function($, _, gettext, HtmlUtils, FormView, formStatusTpl) {
            return FormView.extend({
                el: '#register-form',

                tpl: '#register-tpl',

                events: {
                    'click .js-register': 'submitForm',
                    'click .login-provider': 'thirdPartyAuth',
                    'click .login-provider-msa-migration': 'thirdPartyAuth'
                },

                formType: 'register',

                formStatusTpl: formStatusTpl,

                authWarningJsHook: 'js-auth-warning',

                defaultFormErrorsTitle: gettext('We couldn\'t create your account.'),

                submitButton: '.js-register',

                preRender: function(data) {
                    this.providers = data.thirdPartyAuth.providers || [];
                    this.hasSecondaryProviders = (
                        data.thirdPartyAuth.secondaryProviders && data.thirdPartyAuth.secondaryProviders.length
                    );
                    this.currentProvider = data.thirdPartyAuth.currentProvider || '';
                    this.errorMessage = data.thirdPartyAuth.errorMessage || '';
                    this.platformName = data.platformName;
                    this.autoSubmit = data.thirdPartyAuth.autoSubmitRegForm;
                    this.msaMigrationEnabled = data.msaMigrationEnabled;

                    this.listenTo(this.model, 'sync', this.saveSuccess);
                },

                render: function(html) {
                    var fields = html || '',
                        formErrorsTitle = gettext('An error occurred.');

                    $(this.el).html(_.template(this.tpl)({
                    /* We pass the context object to the template so that
                     * we can perform variable interpolation using sprintf
                     */
                        context: {
                            fields: fields,
                            currentProvider: this.currentProvider,
                            providers: this.providers,
                            hasSecondaryProviders: this.hasSecondaryProviders,
                            platformName: this.platformName,
                            msaMigrationEnabled: this.msaMigrationEnabled
                        }
                    }));

                    this.postRender();

                    if (this.msaMigrationEnabled) {
                        // Hide all form content except the login-providers div.
                        // We need to force users to register with their
                        // Microsoft account


                        if (!this.currentProvider) {
                            this.$form.children()
                                .slice(1)
                                .attr('aria-hidden', 'true')
                                .hide();
                        }
                        $(this.$el)
                            .find('.toggle-form')
                            .attr('aria-hidden', 'true')
                            .hide();
                    }

                    // Must be called after postRender, since postRender sets up $formFeedback.
                    if (this.errorMessage) {
                        this.renderErrors(formErrorsTitle, [this.errorMessage]);
                    } else if (this.currentProvider) {
                        this.renderAuthWarning();
                        // Don't allow user to edit email or name
                        this.$form.find('#register-email, #register-name').prop('disabled', true).addClass('disabled');
                    }
                    if (this.autoSubmit) {
                        $(this.el).hide();
                        $('#register-honor_code').prop('checked', true);
                        this.submitForm();
                    }

                    return this;
                },

                thirdPartyAuth: function(event) {
                    var providerUrl = $(event.currentTarget).data('provider-url') || '';

                    // take user consent for writing non-essential cookies
                    if (window.mscc) {
                        window.mscc.setConsent();
                    }

                    if (providerUrl) {
                        window.location.href = providerUrl;
                    }
                },

                saveSuccess: function() {
                    this.trigger('auth-complete');
                },

                saveError: function(error) {
                    var msgText, msg;
                    $(this.el).show(); // Show in case the form was hidden for auto-submission
                    if (error.status === 409 && error.responseJSON.hasOwnProperty('email')) {
                        msgText = error.responseJSON.email[0].user_message;
                        msg = HtmlUtils.joinHtml(
                            _.sprintf(
                                gettext(msgText + ' If you already have an account, '),
                                {platformName: this.platformName}
                            ),
                            HtmlUtils.HTML(
                                '<a href="/logout?next=%2Flogin" class="btn-neutral btn-register" data-type="login">'
                            ),
                            gettext('login'),
                            HtmlUtils.HTML('</a>'),
                            gettext(' instead.')
                        );
                        this.errors = ['<li>' + msg + '</li>'];
                    } else {
                        this.errors = _.flatten(
                            _.map(
                                // Something is passing this 'undefined'. Protect against this.
                                JSON.parse(error.responseText || '[]'),
                                function(errorList) {
                                    return _.map(
                                        errorList,
                                        function(errorItem) { return '<li>' + errorItem.user_message + '</li>'; }
                                    );
                                }
                            )
                        );
                    }
                    this.renderErrors(this.defaultFormErrorsTitle, this.errors);
                    this.toggleDisableButton(false);
                },

                postFormSubmission: function() {
                    if (_.compact(this.errors).length) {
                    // The form did not get submitted due to validation errors.
                        $(this.el).show(); // Show in case the form was hidden for auto-submission
                    }
                },

                renderAuthWarning: function() {
                    var msgPart1 = gettext('You\'ve successfully signed in with your %(currentProvider)s.'),
                        msgPart2 = gettext(
                            'We just need a little more information before you start learning with %(platformName)s.'
                        ),
                        fullMsg = _.sprintf(
                            msgPart1 + ' ' + msgPart2,
                            {currentProvider: this.currentProvider, platformName: this.platformName}
                        );

                    this.renderFormFeedback(this.formStatusTpl, {
                        jsHook: this.authWarningJsHook,
                        message: fullMsg
                    });
                }
            });
        });
}).call(this, define || RequireJS.define);
