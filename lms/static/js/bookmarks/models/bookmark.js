;(function (define) {

    define(['backbone', 'underscore'], function (Backbone, _) {
        'use strict';

        return Backbone.Model.extend({
            idAttribute: 'id',
            defaults: {
                course_id: '',
                usage_id: '',
                display_name: '',
                path: [],
                created: ''
            },

            parse: function (response) {
                var separator = ' <i class="icon fa fa-caret-right" aria-hidden="true"></i><span class="sr">-</span> ';
                response.breadcrumbTrail = _.pluck(response.path, 'display_name').join(separator);

                // Convert ISO 8601 date string to user friendly format e.g, Month Day, Year
                var time = new Date(response.created);
                var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
                response.userFriendlyDate = MONTHS[time.getMonth()] + ' ' + time.getDay() + ', ' + time.getFullYear();
                return response;
            }
        });
    });

})(define || RequireJS.define);