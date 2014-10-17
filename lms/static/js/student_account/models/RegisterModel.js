var edx = edx || {};

(function($, _, Backbone, gettext) {
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
            termsofservice: false
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
                var query = window.location.search,
                    url = '/dashboard';

                // model.trigger('sync');

                // If query string in url go back to that page
                if ( query.length > 1 ) {
                    url = query.substring( query.indexOf('=') + 1 );
                }

                window.location.href = url;
            })
            .fail( function( error ) {
                console.log('RegisterModel.save() FAILURE!!!!!');
                model.trigger('error', error);
            });
        }
    });
})(jQuery, _, Backbone, gettext);