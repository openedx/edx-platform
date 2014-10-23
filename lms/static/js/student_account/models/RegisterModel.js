var edx = edx || {};

(function($, Backbone) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.RegisterModel = Backbone.Model.extend({

        defaults: {
            email: '',
            name: '',
            username: '',
            password: '',
            level_of_education: '',
            gender: '',
            year_of_birth: '',
            mailing_address: '',
            goals: '',
            honor_code: false
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
