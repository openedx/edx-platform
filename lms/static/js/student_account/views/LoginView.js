var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.LoginView = edx.student.account.FormView.extend({
        el: '#login-form',

        tpl: '#login-tpl',

        events: {
            'click .js-login': 'submitForm',
            'click .forgot-password': 'forgotPassword',
            'click .login-provider': 'thirdPartyAuth'
        },

        formType: 'login',

        requiredStr: '',

        initialize: function( data ) {
            this.tpl = $(this.tpl).html();
            this.fieldTpl = $(this.fieldTpl).html();

            this.buildForm( data.fields );
            this.model = data.model;

            this.providers = data.thirdPartyAuth.providers || [];
            this.currentProvider = data.thirdPartyAuth.currentProvider || '';

            this.listenTo( this.model, 'error', this.saveError );
        },

        render: function( html ) {
            var fields = html || '';

            $(this.el).html( _.template( this.tpl, {
                fields: fields,
                currentProvider: this.currentProvider,
                providers: this.providers
            }));

            this.postRender();

            return this;
        },

        postRender: function() {
            var $container = $(this.el);

            this.$form = $container.find('form');
            this.$errors = $container.find('.submission-error');
            this.$alreadyAuthenticatedMsg =  $container.find('.already-authenticated-msg');

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
        },

        thirdPartyAuth: function( event ) {
            var providerUrl = $(event.target).data('provider-url') || '';
            if (providerUrl) {
                window.location.href = providerUrl;
            } else {
                // TODO -- error handling here
                console.log('No URL available for third party auth provider');
            }
        },

        saveError: function( error ) {
            console.log(error.status, ' error: ', error.responseText);

            /* If we've gotten a 403 error, it means that we've successfully
             * authenticated with a third-party provider, but we haven't
             * linked the account to an EdX account.  In this case,
             * we need to prompt the user to enter a little more information
             * to complete the registration process.
            */
            if (error.status === 403 && error.responseText === "third-party-auth" && this.currentProvider) {
                this.$alreadyAuthenticatedMsg.removeClass("hidden");
            }
            else {
                this.$alreadyAuthenticatedMsg.addClass("hidden");
                // TODO -- display the error
            }

        }
    });

})(jQuery, _, Backbone, gettext);