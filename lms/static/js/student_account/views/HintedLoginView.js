var edx = edx || {};

(function($, _, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.HintedLoginView = Backbone.View.extend({
        el: '#hinted-login-form',

        tpl: '#hinted_login-tpl',

        events: {
            'click .proceed-button': 'proceedWithHintedAuth'
        },

        formType: 'hinted-login',

        initialize: function( data ) {
            this.tpl = $(this.tpl).html();
            this.providers = data.thirdPartyAuth.providers || [];
            this.hintedProvider = _.findWhere(this.providers, {id: data.hintedProvider})
            this.platformName = data.platformName;

        },

        render: function() {
            $(this.el).html( _.template( this.tpl, {
                // We pass the context object to the template so that
                // we can perform variable interpolation using sprintf
                providers: this.providers,
                platformName: this.platformName,
                hintedProvider: this.hintedProvider
            }));

            return this;
        },

        proceedWithHintedAuth: function( event ) {
            this.redirect(this.hintedProvider.loginUrl);
        },

        /**
         * Redirect to a URL.  Mainly useful for mocking out in tests.
         * @param  {string} url The URL to redirect to.
         */
        redirect: function( url ) {
            window.location.href = url;
        }
    });
})(jQuery, _, gettext);
