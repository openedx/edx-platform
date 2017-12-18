(function(define) {
    'use strict';
    define(['jquery', 'underscore', 'backbone'],
        function($, _, Backbone) {
            return Backbone.View.extend({
                el: '#institution_login-form',

                initialize: function(data) {
                    var tpl = data.mode == 'register' ? '#institution_register-tpl' : '#institution_login-tpl';
                    this.tpl = $(tpl).html();
                    this.providers = data.thirdPartyAuth.secondaryProviders || [];
                    this.platformName = data.platformName;
                },

                render: function() {
                    $(this.el).html(_.template(this.tpl)({
                    // We pass the context object to the template so that
                    // we can perform variable interpolation using sprintf
                        providers: this.providers,
                        platformName: this.platformName
                    }));

                    return this;
                }
            });
        });
}).call(this, define || RequireJS.define);
