(function(define) {
    define(['backbone'], function(Backbone) {
        'use strict';

        return Backbone.Model.extend({
            defaults: {
                modes: [],
                course: '',
                enrollment_start: '',
                number: '',
                content: {
                    overview: '',
                    display_name: '',
                    number: ''
                },
                start: '',
                image_url: '',
                org: '',
                id: '',
                partner_logo_url: ''
            }
        });
    });
}(define || RequireJS.define));
