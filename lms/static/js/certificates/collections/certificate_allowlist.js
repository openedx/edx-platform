// Backbone.js Application Collection: CertificateAllowlist
/* global define, RequireJS */

(function(define) {
    'use strict';
    define([
        'backbone',
        'gettext',
        'js/certificates/models/certificate_exception'
    ],

        function(Backbone, gettext, CertificateExceptionModel) {
            var CertificateAllowlist = Backbone.Collection.extend({
                model: CertificateExceptionModel,

                initialize: function(attrs, options) {
                    this.url = options.url;
                    this.generate_certificates_url = options.generate_certificates_url;
                },

                getModel: function(attrs) {
                    var model = this.findWhere({user_name: attrs.user_name});
                    if (attrs.user_name && model) {
                        return model;
                    }

                    model = this.findWhere({user_email: attrs.user_email});
                    if (attrs.user_email && model) {
                        return model;
                    }

                    return undefined;
                },

                sync: function(options, appended_url) {
                    var filtered = [];
                    if (appended_url === 'new') {
                        filtered = this.filter(function(model) {
                            return model.get('new');
                        });
                    }
                    var url = this.generate_certificates_url + appended_url;
                    Backbone.sync(
                        'create',
                        new CertificateAllowlist(filtered, {url: url, generate_certificates_url: url}),
                        options
                    );
                },

                update: function(data) {
                    _.each(data, function(item) {
                        var certificate_exception_model =
                            this.getModel({user_name: item.user_name, user_email: item.user_email});
                        certificate_exception_model.set(item);
                    }, this);
                }
            });

            return CertificateAllowlist;
        }
    );
}).call(this, define || RequireJS.define);
