;(function (define) {

    define(['backbone'], function (Backbone) {
        'use strict';

        return Backbone.Model.extend({
            idAttribute: 'id',
            defaults: {
                course_id: '',
                usage_id: '',
                display_name: '',
                path: [],
                created: ''
            }
        });
    });

})(define || RequireJS.define);