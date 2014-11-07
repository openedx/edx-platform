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
            },

            timeFormat: 'hh:mmtt', // For example: 12:59PM
            dateFormat: 'MMMM dd, yyyy', // For example: November 11, 2014

            parse: function (attributes) {
                if (attributes.updated) {
                    attributes.updated = new Date(attributes.updated);
                }
                if (attributes.created) {
                    attributes.created = new Date(attributes.created);
                }
                return attributes;
            },

            /**
             * Returns date string in the following format:
             * `November 11, 2014 at 12:59PM`.
             * @param {Date} datetime Date used to convert to date string.
             * @return {String}
             */
            getDateTime: function (datetime) {
                var datetimeString = gettext('%(date)s at %(time)s');

                return interpolate(datetimeString, {
                    date: datetime.toString(this.dateFormat),
                    time: datetime.toString(this.timeFormat)
                }, true);
            },

            /**
             * Returns context for the views.
             * @return {Object}
             */
            toContext: function () {
                return $.extend(true, {}, this.attributes, {
                    created: this.getDateTime(this.get('created')),
                    updated: this.getDateTime(this.get('updated'))
                });
            }
        });

        return NoteModel;
    });
}).call(this, define || RequireJS.define, gettext, interpolate);
