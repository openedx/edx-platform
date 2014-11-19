;(function (define, gettext, interpolate, undefined) {
    'use strict';
    define(['jquery', 'backbone', 'date'], function ($, Backbone) {
        var NoteModel = Backbone.Model.extend({
            defaults: {
                'id': null,
                'created': null,
                'updated': null,
                'user': null,
                'usage_id': null,
                'course_id': null,
                'text': null,
                'quote': null,
                'unit': {
                    'display_name': null,
                    'url': null
                },
                'ranges': []
            }
        });

        return NoteModel;
    });
}).call(this, define || RequireJS.define, gettext, interpolate);
