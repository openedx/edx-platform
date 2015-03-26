var edx = edx || {};

(function($, Backbone) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.PasswordResetModel = Backbone.Model.extend({

        defaults: {
            email: ''
        },

        ajaxType: '',

        urlRoot: '',

        initialize: function( attributes, options ) {
            this.ajaxType = options.method;
            this.urlRoot = options.url;
        },

        sync: function( method, model ) {
            var headers = {
                'X-CSRFToken': $.cookie('csrftoken')
            };

            // Only expects an email address.
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
