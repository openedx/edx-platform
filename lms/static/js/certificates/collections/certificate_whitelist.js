// Backbone.js Application Collection: CertificateWhiteList
/*global define, RequireJS */

;(function(define){
    'use strict';
    define([
            'backbone',
            'gettext',
            'js/certificates/models/certificate_exception'
        ],

        function(Backbone, gettext, CertificateExceptionModel){

            var CertificateWhiteList =  Backbone.Collection.extend({
                model: CertificateExceptionModel,

                initialize: function(attrs, options){
                    this.url = options.url;
                },

                getModel: function(attrs){
                    var model = this.findWhere({user_name: attrs.user_name});
                    if(attrs.user_name && model){
                        return model;
                    }

                    model = this.findWhere({user_email: attrs.user_email});
                    if(attrs.user_email && model){
                        return model;
                    }

                    return undefined;
                },

                sync: function(options, appended_url){
                    var filtered = this.filter(function(model){
                        return model.isNew();
                    });

                    Backbone.sync(
                        'create',
                        new CertificateWhiteList(filtered, {url: this.url + appended_url}),
                        options
                    );
                },

                update: function(data){
                    _.each(data, function(item){
                        var certificate_exception_model =
                            this.getModel({user_name: item.user_name, user_email: item.user_email});
                        certificate_exception_model.set(item);
                    }, this);
                }
            });

            return CertificateWhiteList;
        }
    );
}).call(this, define || RequireJS.define);