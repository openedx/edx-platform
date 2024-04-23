(function(define) {
    'use strict';

    define(['jquery', 'backbone', 'jquery.url'],
        function($, Backbone) {
            return Backbone.Model.extend({
                defaults: {
                    email: '',
                    name: '',
                    username: '',
                    password: '',
                    level_of_education: '',
                    gender: '',
                    year_of_birth: '',
                    mailing_address: '',
                    goals: ''
                },
                ajaxType: '',
                urlRoot: '',
                is_auto_generated_username_enabled: false,

                initialize: function(attributes, options) {
                    this.ajaxType = options.method;
                    this.urlRoot = options.url;
                    this.nextUrl = options.nextUrl;
                    this.is_auto_generated_username_enabled = options.is_auto_generated_username_enabled;
                },

                sync: function(method, model) {
                    var headers = {'X-CSRFToken': $.cookie('csrftoken')},
                        data = {next: model.nextUrl},
                        courseId = $.url('?course_id');

                    // If there is a course ID in the query string param,
                    // send that to the server as well so it can be included
                    // in analytics events.
                    if (courseId) {
                        data.course_id = decodeURIComponent(courseId);
                    }

                   // Filter out username if auto-generation is enabled
                    var attributesToSend = _.omit(model.attributes, function(value, key) {
                        // Exclude username field if auto-generated username is enabled
                        return key === 'username' && model.is_auto_generated_username_enabled;
                    });

                    // Include all form fields and analytics info in the data sent to the server
                    $.extend(data, attributesToSend);

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
