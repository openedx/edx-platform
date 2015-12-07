/**
 * Model for a topic.
 */
(function (define) {
    'use strict';
    define(['backbone'], function (Backbone) {
        var Topic = Backbone.Model.extend({
            defaults: {
                name: '',
                description: '',
                team_count: 0,
                id: ''
            },

            initialize: function(options) {
                this.url = options.url;
            }
        });
        return Topic;
    });
}).call(this, define || RequireJS.define);
