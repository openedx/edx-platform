/**
 * Model for a team.
 */
(function (define) {
    'use strict';
    define(['backbone'], function (Backbone) {
        var Team = Backbone.Model.extend({
            defaults: {
                id: null,
                name: '',
                course_id: '',
                topic_id: '',
                date_created: '',
                description: '',
                country: '',
                language: '',
                membership: [],
                last_activity_at: ''
            },

            initialize: function(options) {
                this.url = options.url;
            }
        });
        return Team;
    });
}).call(this, define || RequireJS.define);
