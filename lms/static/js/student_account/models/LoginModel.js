(function(define) {
    'use strict';
    define([
        'jquery',
        'backbone',
        'jquery.url'
    ], function($, Backbone) {
        return Backbone.Model.extend({
            defaults: {
                email: '',
                password: ''
            },

            ajaxType: '',
            urlRoot: '',

            initialize: function(attributes, options) {
                this.ajaxType = options.method;
                this.urlRoot = options.url;
            },

            sync: function(method, model) {
                var headers = {'X-CSRFToken': $.cookie('csrftoken')},
                    data = {},
                    analytics,
                    courseId = $.url('?course_id');

                // If there is a course ID in the query string param,
                // send that to the server as well so it can be included
                // in analytics events.
                if (courseId) {
                    analytics = JSON.stringify({
                        enroll_course_id: decodeURIComponent(courseId)
                    });
                }

                // Include all form fields and analytics info in the data sent to the server
                $.extend(data, model.attributes, {analytics: analytics});

                $.ajax({
                    url: model.urlRoot,
                    type: model.ajaxType,
                    data: data,
                    headers: headers,
                    success: function() {
                        model.trigger('sync');
                    },
                    error: function(error) {
                        model.trigger('error', error);
                    }
                });
            }
        });
    });
}).call(this, define || RequireJS.define);
