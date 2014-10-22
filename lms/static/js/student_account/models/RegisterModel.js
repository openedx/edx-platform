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
                var enrollment = edx.student.account.EnrollmentInterface,
                    query = new URI(window.location.search),
                    url = '/dashboard',
                    query_map = query.search(true),
                    next = '';

                // check for forwarding url
                if("next" in query_map) {
                    next = query_map['next'];
                    if(!window.isExternal(next)){
                        url = next;
                    }
                }

                model.trigger('sync');

                // if we need to enroll in the course, mark as enrolled
                if('enrollment_action' in query_map && query_map['enrollment_action'] === 'enroll'){
                    enrollment.enroll(query_map['course_id'], url);
                }
                else {
                    window.location.href = url;
                }
            })
            .fail( function( error ) {
                model.trigger('error', error);
            });
        }
    });
})(jQuery, _, Backbone, gettext);
