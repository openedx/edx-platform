;(function (define) {

define(['backbone'], function (Backbone) {
    'use strict';

    return Backbone.Model.extend({
        defaults: {
            content: {
                display_name: '',
                number: '',
                overview: '',
                short_description: ''
            },
            course: '',
            enrollment_start: '',
            id: '',
            image_url: '',
            number: '',
            start: '',
            effort: '',
            org: ''
        }
    });

});

})(define || RequireJS.define);
