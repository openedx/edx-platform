var edx = edx || {};

(function($, _, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.RegisterView = edx.student.account.FormView.extend({
        el: '#register-form',

        tpl: '#register-tpl',

        events: {
            'click .js-register': 'submitForm',
            'click .login-provider': 'thirdPartyAuth'
        },

        formType: 'register',

        preRender: function( data ) {
            this.providers = data.thirdPartyAuth.providers || [];
            this.currentProvider = data.thirdPartyAuth.currentProvider || '';
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

        thirdPartyAuth: function( event ) {
            var providerUrl = $(event.target).data('provider-url') || '';

            if (providerUrl) {
                window.location.href = providerUrl;
            } else {
                // TODO -- error handling here
                console.log('No URL available for third party auth provider');
            }
        }
    });

})(jQuery, _, gettext);
