;(function (define) {
    'use strict';
    define([
            'jquery',
            'underscore',
            'gettext',
            'js/student_account/views/FormView'
        ],
        function($, _, gettext, FormView) {

        return FormView.extend({
            el: '#login-form',
            tpl: '#login-tpl',
            events: {
                'click .js-login': 'submitForm',
                'click .forgot-password': 'forgotPassword',
                'click .login-provider': 'thirdPartyAuth'
            },
            formType: 'login',
            requiredStr: '',
            submitButton: '.js-login',

            preRender: function( data ) {
                this.providers = data.thirdPartyAuth.providers || [];
                this.hasSecondaryProviders = (
                    data.thirdPartyAuth.secondaryProviders && data.thirdPartyAuth.secondaryProviders.length
                );
                this.currentProvider = data.thirdPartyAuth.currentProvider || '';
                this.errorMessage = data.thirdPartyAuth.errorMessage || '';
                this.platformName = data.platformName;
                this.resetModel = data.resetModel;

                this.listenTo( this.model, 'sync', this.saveSuccess );
                this.listenTo( this.resetModel, 'sync', this.resetEmail );
            },

            render: function( html ) {
                var fields = html || '';

                $(this.el).html( _.template( this.tpl, {
                    // We pass the context object to the template so that
                    // we can perform variable interpolation using sprintf
                    context: {
                        fields: fields,
                        currentProvider: this.currentProvider,
                        errorMessage: this.errorMessage,
                        providers: this.providers,
                        hasSecondaryProviders: this.hasSecondaryProviders,
                        platformName: this.platformName
                    }
                }));

                this.postRender();

                return this;
            },

            postRender: function() {
                this.$container = $(this.el);

                this.$form = this.$container.find('form');
                this.$errors = this.$container.find('.submission-error');
                this.$resetSuccess = this.$container.find('.js-reset-success');
                this.$authError = this.$container.find('.already-authenticated-msg');
                this.$submitButton = this.$container.find(this.submitButton);

                /* If we're already authenticated with a third-party
                 * provider, try logging in.  The easiest way to do this
                 * is to simply submit the form.
                 */
                if (this.currentProvider) {
                    this.model.save();
                }
            },

            forgotPassword: function( event ) {
                event.preventDefault();

                this.trigger('password-help');
                this.element.hide( this.$resetSuccess );
            },

            postFormSubmission: function() {
                this.element.hide( this.$resetSuccess );
            },

            resetEmail: function() {
                this.element.hide( this.$errors );
                this.element.show( this.$resetSuccess );
            },

            thirdPartyAuth: function( event ) {
                var providerUrl = $(event.currentTarget).data('provider-url') || '';

                if (providerUrl) {
                    window.location.href = providerUrl;
                }
            },

            saveSuccess: function() {
                this.trigger('auth-complete');
                this.element.hide( this.$resetSuccess );
            },

            saveError: function( error ) {
                var url;
                var queryParameters = (function getUrlVars() {
                    // http://stackoverflow.com/a/4656873
                    var vars = [], hash;
                    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
                    for(var i = 0; i < hashes.length; i++)
                    {
                        hash = hashes[i].split('=');
                        vars.push(hash[0]);
                        vars[hash[0]] = hash[1];
                    }
                    return vars;
                }());
                if(error.status === 418) {
                    // Hijack the response for Shibboleth redirects
                    url = error.responseText;
                    if(url) {
                        if(queryParameters['next']) {
                            url = url + '?next=' + queryParameters['next'];
                        }
                        window.location = url;
                        return;
                    }
                }
                if (error.status === 0) {
                    this.errors = ['<li>' + gettext('Please check your internet connection and try again.') + '</li>'];
                }
                else {
                    this.errors = ['<li>' + error.responseText + '</li>'];
                }
                this.setErrors();
                this.element.hide( this.$resetSuccess );

                /* If we've gotten a 403 error, it means that we've successfully
                 * authenticated with a third-party provider, but we haven't
                 * linked the account to an EdX account.  In this case,
                 * we need to prompt the user to enter a little more information
                 * to complete the registration process.
                 */
                if ( error.status === 403 &&
                     error.responseText === 'third-party-auth' &&
                     this.currentProvider ) {
                    this.element.show( this.$authError );
                    this.element.hide( this.$errors );
                } else {
                    this.element.hide( this.$authError );
                    this.element.show( this.$errors );
                }
                this.toggleDisableButton(false);
            }
        });
    });
}).call(this, define || RequireJS.define);

