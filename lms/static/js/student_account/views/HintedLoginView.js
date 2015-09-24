;(function (define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone'],
        function($, _, Backbone) {

        return Backbone.View.extend({
            el: '#hinted-login-form',

            tpl: '#hinted_login-tpl',

            events: {
                'click .proceed-button': 'proceedWithHintedAuth'
            },

            formType: 'hinted-login',

            initialize: function( data ) {
                this.tpl = $(this.tpl).html();
                this.hintedProvider = (
                    _.findWhere(data.thirdPartyAuth.providers, {id: data.hintedProvider}) ||
                    _.findWhere(data.thirdPartyAuth.secondaryProviders, {id: data.hintedProvider})
                );
            },

            render: function() {
                $(this.el).html( _.template( this.tpl, {
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
    });
}).call(this, define || RequireJS.define);
