(function(define) {
    'use strict';
    define([
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/string-utils',
        'js/student_account/views/FormView',
        'text!templates/student_account/form_status.underscore'
    ],
        function(
            $, _, gettext,
            StringUtils,
            FormView,
            formStatusTpl
        ) {
            return FormView.extend({
                el: '#register-form',
                tpl: '#register-tpl',
                validationUrl: '/api/user/v1/validation/registration',
                events: {
                    'click .js-register': 'submitForm',
                    'click .login-provider': 'thirdPartyAuth',
                    'click input[required][type="checkbox"]': 'liveValidateHandler',
                    'blur input[required], textarea[required], select[required]': 'liveValidateHandler',
                    'focus input[required], textarea[required], select[required]': 'handleRequiredInputFocus'
                },
                liveValidationFields: [
                    'name',
                    'username',
                    'password',
                    'email',
                    'confirm_email',
                    'country',
                    'honor_code',
                    'terms_of_service'
                ],
                formType: 'register',
                formStatusTpl: formStatusTpl,
                authWarningJsHook: 'js-auth-warning',
                defaultFormErrorsTitle: gettext('We couldn\'t create your account.'),
                submitButton: '.js-register',
                positiveValidationIcon: 'fa-check',
                negativeValidationIcon: 'fa-exclamation',
                successfulValidationDisplaySeconds: 3,
            // These are reset to true on form submission.
                positiveValidationEnabled: true,
                negativeValidationEnabled: true,

                preRender: function(data) {
                    this.providers = data.thirdPartyAuth.providers || [];
                    this.hasSecondaryProviders = (
                        data.thirdPartyAuth.secondaryProviders && data.thirdPartyAuth.secondaryProviders.length
                    );
                    this.currentProvider = data.thirdPartyAuth.currentProvider || '';
                    this.errorMessage = data.thirdPartyAuth.errorMessage || '';
                    this.platformName = data.platformName;
                    this.autoSubmit = data.thirdPartyAuth.autoSubmitRegForm;
                    this.hideAuthWarnings = data.hideAuthWarnings;
                    this.autoRegisterWelcomeMessage = data.thirdPartyAuth.autoRegisterWelcomeMessage || '';
                    this.registerFormSubmitButtonText =
                        data.thirdPartyAuth.registerFormSubmitButtonText || _('Create Account');

                    this.listenTo(this.model, 'sync', this.saveSuccess);
                    this.listenTo(this.model, 'validation', this.renderLiveValidations);
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
                            autoRegisterWelcomeMessage: this.autoRegisterWelcomeMessage,
                            registerFormSubmitButtonText: this.registerFormSubmitButtonText
                        }
                    }));

                    this.postRender();

                    // Must be called after postRender, since postRender sets up $formFeedback.
                    if (this.errorMessage) {
                        this.renderErrors(formErrorsTitle, [this.errorMessage]);
                    } else if (this.currentProvider && !this.hideAuthWarnings) {
                        this.renderAuthWarning();
                    }

                    if (this.autoSubmit) {
                        $(this.el).hide();
                        $('#register-honor_code').prop('checked', true);
                        this.submitForm();
                    }

                    return this;
                },

                hideRequiredMessageExceptOnError: function($el) {
                    // We only handle blur if not in an error state.
                    if (!$el.hasClass('error')) {
                        this.hideRequiredMessage($el);
                    }
                },

                hideRequiredMessage: function($el) {
                    this.doOnInputLabel($el, function($label) {
                        $label.addClass('hidden');
                    });
                },

                doOnInputLabel: function($el, action) {
                    var $label = this.getRequiredTextLabel($el);
                    action($label);
                },

                handleRequiredInputFocus: function(event) {
                    var $el = $(event.currentTarget);
                    // Avoid rendering for required checkboxes.
                    if ($el.attr('type') !== 'checkbox') {
                        this.renderRequiredMessage($el);
                    }
                    if ($el.hasClass('error')) {
                        this.doOnInputLabel($el, function($label) {
                            $label.addClass('error');
                        });
                    }
                },

                renderRequiredMessage: function($el) {
                    this.doOnInputLabel($el, function($label) {
                        $label.removeClass('hidden').text(gettext('(required)'));
                    });
                },

                getRequiredTextLabel: function($el) {
                    return $('#' + $el.attr('id') + '-required-label');
                },

                renderLiveValidations: function($el, decisions) {
                    var $label = this.getLabel($el),
                        $requiredTextLabel = this.getRequiredTextLabel($el),
                        $icon = this.getIcon($el),
                        $errorTip = this.getErrorTip($el),
                        name = $el.attr('name'),
                        type = $el.attr('type'),
                        isCheckbox = type === 'checkbox',
                        hasError = decisions.validation_decisions[name] !== '',
                        error = isCheckbox ? '' : decisions.validation_decisions[name];

                    if (hasError && this.negativeValidationEnabled) {
                        this.renderLiveValidationError($el, $label, $requiredTextLabel, $icon, $errorTip, error);
                    } else if (this.positiveValidationEnabled) {
                        this.renderLiveValidationSuccess($el, $label, $requiredTextLabel, $icon, $errorTip);
                    }
                },

                getLabel: function($el) {
                    return this.$form.find('label[for=' + $el.attr('id') + ']');
                },

                getIcon: function($el) {
                    return $('#' + $el.attr('id') + '-validation-icon');
                },

                getErrorTip: function($el) {
                    return $('#' + $el.attr('id') + '-validation-error-msg');
                },

                getFieldTimeout: function($el) {
                    return $('#' + $el.attr('id')).attr('timeout-id') || null;
                },

                setFieldTimeout: function($el, time, action) {
                    $el.attr('timeout-id', setTimeout(action, time));
                },

                clearFieldTimeout: function($el) {
                    var timeout = this.getFieldTimeout($el);
                    if (timeout) {
                        clearTimeout(this.getFieldTimeout($el));
                        $el.removeAttr('timeout-id');
                    }
                },

                renderLiveValidationError: function($el, $label, $req, $icon, $tip, error) {
                    this.removeLiveValidationIndicators(
                        $el, $label, $req, $icon,
                        'success', this.positiveValidationIcon
                    );
                    this.addLiveValidationIndicators(
                        $el, $label, $req, $icon, $tip,
                        'error', this.negativeValidationIcon, error
                    );
                    this.renderRequiredMessage($el);
                },

                renderLiveValidationSuccess: function($el, $label, $req, $icon, $tip) {
                    var self = this,
                        validationFadeTime = this.successfulValidationDisplaySeconds * 1000;
                    this.removeLiveValidationIndicators(
                        $el, $label, $req, $icon,
                        'error', this.negativeValidationIcon
                    );
                    this.addLiveValidationIndicators(
                        $el, $label, $req, $icon, $tip,
                        'success', this.positiveValidationIcon, ''
                    );
                    this.hideRequiredMessage($el);

                    // Hide success indicators after some time.
                    this.clearFieldTimeout($el);
                    this.setFieldTimeout($el, validationFadeTime, function() {
                        self.removeLiveValidationIndicators(
                            $el, $label, $req, $icon,
                            'success', self.positiveValidationIcon
                        );
                        self.clearFieldTimeout($el);
                    });
                },

                addLiveValidationIndicators: function($el, $label, $req, $icon, $tip, indicator, icon, msg) {
                    $el.addClass(indicator);
                    $label.addClass(indicator);
                    $req.addClass(indicator);
                    $icon.addClass(indicator + ' ' + icon);
                    $tip.text(msg);
                },

                removeLiveValidationIndicators: function($el, $label, $req, $icon, indicator, icon) {
                    $el.removeClass(indicator);
                    $label.removeClass(indicator);
                    $req.removeClass(indicator);
                    $icon.removeClass(indicator + ' ' + icon);
                },

                thirdPartyAuth: function(event) {
                    var providerUrl = $(event.currentTarget).data('provider-url') || '';

                    if (providerUrl) {
                        window.location.href = providerUrl;
                    }
                },

                saveSuccess: function() {
                    this.trigger('auth-complete');
                },

                saveError: function(error) {
                    $(this.el).show(); // Show in case the form was hidden for auto-submission
                    this.errors = _.flatten(
                        _.map(
                            // Something is passing this 'undefined'. Protect against this.
                            JSON.parse(error.responseText || '[]'),
                            function(errorList) {
                                return _.map(
                                    errorList,
                                    function(errorItem) {
                                        return StringUtils.interpolate('<li>{error}</li>', {
                                            error: errorItem.user_message
                                        });
                                    }
                                );
                            }
                        )
                    );
                    this.renderErrors(this.defaultFormErrorsTitle, this.errors);
                    this.scrollToFormFeedback();
                    this.toggleDisableButton(false);
                },

                postFormSubmission: function() {
                    if (_.compact(this.errors).length) {
                    // The form did not get submitted due to validation errors.
                        $(this.el).show(); // Show in case the form was hidden for auto-submission
                    }
                },

                resetValidationVariables: function() {
                    this.positiveValidationEnabled = true;
                    this.negativeValidationEnabled = true;
                },

                renderAuthWarning: function() {
                    var msgPart1 = gettext('You\'ve successfully signed into %(currentProvider)s.'),
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
                },

                submitForm: function(event) { // eslint-disable-line no-unused-vars
                    var elements = this.$form[0].elements,
                        $el,
                        i;

                // As per requirements, disable positive validation for submission.
                    this.positiveValidationEnabled = false;

                    for (i = 0; i < elements.length; i++) {
                        $el = $(elements[i]);

                        // Simulate live validation.
                        if ($el.attr('required')) {
                            $el.blur();
                        }
                    }

                    FormView.prototype.submitForm.apply(this, arguments);
                },

                getFormData: function() {
                    var obj = FormView.prototype.getFormData.apply(this, arguments),
                        $emailElement = this.$form.find('input[name=email]'),
                        $confirmEmail = this.$form.find('input[name=confirm_email]');

                    if ($confirmEmail.length) {
                        if (!$confirmEmail.val() || ($emailElement.val() !== $confirmEmail.val())) {
                            this.errors.push(StringUtils.interpolate('<li>{error}</li>', {
                                error: $confirmEmail.data('errormsg-required')
                            }));
                        }
                        obj.confirm_email = $confirmEmail.val();
                    }

                    return obj;
                },

                liveValidateHandler: function(event) {
                    var $el = $(event.currentTarget);
                    // Until we get a back-end that can handle all available
                    // registration fields, we do some generic validation here.
                    if (this.inLiveValidationFields($el)) {
                        if ($el.attr('type') === 'checkbox') {
                            this.liveValidateCheckbox($el);
                        } else {
                            this.liveValidate($el);
                        }
                    } else {
                        this.genericLiveValidateHandler($el);
                    }
                    // On blur, we do exactly as the function name says, no matter which input.
                    this.hideRequiredMessageExceptOnError($el);
                },

                liveValidate: function($el) {
                    var data = {},
                        field,
                        i;
                    for (i = 0; i < this.liveValidationFields.length; ++i) {
                        field = this.liveValidationFields[i];
                        data[field] = $('#register-' + field).val();
                    }
                    FormView.prototype.liveValidate(
                        $el, this.validationUrl, 'json', data, 'POST', this.model
                    );
                },

                liveValidateCheckbox: function($checkbox) {
                    var validationDecisions = {validation_decisions: {}},
                        decisions = validationDecisions.validation_decisions,
                        name = $checkbox.attr('name'),
                        checked = $checkbox.is(':checked'),
                        error = $checkbox.data('errormsg-required');
                    decisions[name] = checked ? '' : error;
                    this.renderLiveValidations($checkbox, validationDecisions);
                },

                genericLiveValidateHandler: function($el) {
                    var elementType = $el.attr('type');
                    if (elementType === 'checkbox') {
                    // We are already validating checkboxes in a generic way.
                        this.liveValidateCheckbox($el);
                    } else {
                        this.genericLiveValidate($el);
                    }
                },

                genericLiveValidate: function($el) {
                    var validationDecisions = {validation_decisions: {}},
                        decisions = validationDecisions.validation_decisions,
                        name = $el.attr('name'),
                        error = $el.data('errormsg-required');
                    decisions[name] = $el.val() ? '' : error;
                    this.renderLiveValidations($el, validationDecisions);
                }
            });
        });
}).call(this, define || RequireJS.define);
