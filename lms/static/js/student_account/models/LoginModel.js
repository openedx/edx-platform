var edx = edx || {};

(function($, Backbone) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.LoginModel = Backbone.Model.extend({

        defaults: {
            email: '',
            password: '',
            remember: false
        },

        ajaxType: '',

        urlRoot: '',

        initialize: function( obj ) {
            this.ajaxType = obj.method;
            this.urlRoot = obj.url;
        },

        sync: function(method, model) {
            var headers = {
                'X-CSRFToken': $.cookie('csrftoken')
            };

            $.ajax({
                url: model.urlRoot,
                type: model.ajaxType,
                data: model.attributes,
                headers: headers,
                success: function() {
                    model.trigger('sync');
                },
                error: function( error ) {
                    model.trigger('error', error);
                }
            });
        }
    });
})(jQuery, Backbone);
