var edx = edx || {};

(function($, _, Backbone, gettext) {
    'use strict';

    edx.student = edx.student || {};
    edx.student.account = edx.student.account || {};

    edx.student.account.PasswordResetModel = Backbone.Model.extend({

        defaults: {
            email: ''
        },

        urlRoot: '/resetMe',

        sync: function(method, model) {
            var headers = {
                'X-CSRFToken': $.cookie('csrftoken')
            };

            // Is just expecting email address
            $.ajax({
                url: model.urlRoot,
                type: 'POST',
                data: model.attributes,
                headers: headers
            })
            .done(function() {
                var query = window.location.search,
                    url = '/dashboard';

                model.trigger('success');
            })
            .fail( function( error ) {
                console.log('RegisterModel.save() FAILURE!!!!!');
                model.trigger('error', error);
            });
        }
    });
})(jQuery, _, Backbone, gettext);