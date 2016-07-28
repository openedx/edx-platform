;(function (define) {
    'use strict';
    define([
            'jquery',
            'underscore',
            'js/student_account/views/FormView'
        ],
        function($, _, FormView) {

        return FormView.extend({
            el: '#register-form',

            tpl: '#register-tpl',

            events: {
                'click .js-register': 'submitForm',
                'click .login-provider': 'thirdPartyAuth'
            },

            formType: 'register',

            submitButton: '.js-register',

            preRender: function( data ) {
                this.providers = data.thirdPartyAuth.providers || [];
                this.hasSecondaryProviders = (
                    data.thirdPartyAuth.secondaryProviders && data.thirdPartyAuth.secondaryProviders.length
                );
                this.currentProvider = data.thirdPartyAuth.currentProvider || '';
                this.errorMessage = data.thirdPartyAuth.errorMessage || '';
                this.platformName = data.platformName;
                this.autoSubmit = data.thirdPartyAuth.autoSubmitRegForm;
                this.isNonMicrositeTheme = data.isNonMicrositeTheme;

                this.listenTo( this.model, 'sync', this.saveSuccess );
            },

            render: function( html ) {
                var fields = html || '';

                $(this.el).html( _.template( this.tpl, {
                    /* We pass the context object to the template so that
                     * we can perform variable interpolation using sprintf
                     */
                    context: {
                        fields: fields,
                        currentProvider: this.currentProvider,
                        errorMessage: this.errorMessage,
                        providers: this.providers,
                        hasSecondaryProviders: this.hasSecondaryProviders,
                        isNonMicrositeTheme: this.isNonMicrositeTheme,
                        platformName: this.platformName
                    }
                }));

                this.postRender();

                if (this.autoSubmit) {
                    $(this.el).hide();
                    $('#register-honor_code').prop('checked', true);
                    this.submitForm();
                }

                return this;
            },

            thirdPartyAuth: function( event ) {
                var providerUrl = $(event.currentTarget).data('provider-url') || '';

                if ( providerUrl ) {
                    window.location.href = providerUrl;
                }
            },

            saveSuccess: function() {
                this.trigger('auth-complete');
            },

            saveError: function( error ) {
                $(this.el).show(); // Show in case the form was hidden for auto-submission
                this.errors = _.flatten(
                    _.map(
                        JSON.parse(error.responseText),
                        function(error_list) {
                            return _.map(
                                error_list,
                                function(error) { return '<li>' + error.user_message + '</li>'; }
                            );
                        }
                    )
                );
                this.setErrors();
                this.toggleDisableButton(false);
            },

            postFormSubmission: function() {
                if (_.compact(this.errors).length) {
                    // The form did not get submitted due to validation errors.
                    $(this.el).show(); // Show in case the form was hidden for auto-submission
                }
            }
        });
    });
}).call(this, define || RequireJS.define);
