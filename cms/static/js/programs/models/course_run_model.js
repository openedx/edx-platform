define([
    'backbone'
],
    function(Backbone) {
        'use strict';

        return Backbone.Model.extend({
            defaults: {
                course_key: '',
                mode_slug: 'verified',
                sku: '',
                start_date: '',
                run_key: ''
            }
        });
    }
);
