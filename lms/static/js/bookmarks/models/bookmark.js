;(function (define) {
    'use strict';
    define(['backbone'], function (Backbone) {

        return Backbone.Model.extend({
            idAttribute: 'id',
            defaults: {
                course_id: '',
                usage_id: '',
                display_name: '',
                path: [],
                created: ''
            },

            blockUrl: function () {
                return '/courses/' + this.get('course_id') + '/jump_to/' + this.get('usage_id');
            }
        });
    });

})(define || RequireJS.define);
