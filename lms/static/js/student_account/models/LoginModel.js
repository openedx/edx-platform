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

        urlRoot: '',

        initialize: function( obj ) {
            this.urlRoot = obj.url;
        },

        sync: function(method, model) {
            var headers = {
                'X-CSRFToken': $.cookie('csrftoken')
            };

            $.ajax({
                url: model.urlRoot,
                type: 'POST',
                data: model.attributes,
                headers: headers
            })
            .done(function() {
                model.trigger('sync');
            })
            .fail( function( error ) {
                model.trigger('error', error);
            });
        }
    });
})(jQuery, Backbone);
