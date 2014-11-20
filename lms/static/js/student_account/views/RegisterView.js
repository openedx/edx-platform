define([
        'gettext',
        'jquery',
        'underscore',
        'js/student_account/views/FormView',
        'text!js/student_account/templates/register.underscore'
    ],
    function( gettext, $, _, FormView, registerTpl ) {

        'use strict';

        return FormView.extend({
            el: '#register-form',

            tpl: registerTpl,

            events: {
                'click .js-register': 'submitForm',
                'click .login-provider': 'thirdPartyAuth'
            },

            formType: 'register',

            submitButton: '.js-register',

            preRender: function( data ) {
                this.providers = data.thirdPartyAuth.providers || [];
                this.currentProvider = data.thirdPartyAuth.currentProvider || '';
                this.platformName = data.platformName;

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
                        providers: this.providers,
                        platformName: this.platformName
                    }
                }));

                this.postRender();

                return this;
            },

            thirdPartyAuth: function( event ) {
                var providerUrl = $(event.target).data('provider-url') || '';

                if ( providerUrl ) {
                    window.location.href = providerUrl;
                }
            },

            saveSuccess: function() {
                this.trigger('auth-complete');
            }

        });
    }
);
