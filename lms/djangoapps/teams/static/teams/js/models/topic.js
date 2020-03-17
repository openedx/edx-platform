/**
 * Model for a topic.
 */
(function(define) {
    'use strict';
    define(['backbone'], function(Backbone) {
        var Topic = Backbone.Model.extend({
            defaults: {
                name: '',
                description: '',
                team_count: 0,
                id: '',
                type: 'open',
                max_team_size: null
            },

            initialize: function(options) {
                this.url = options.url;
            },

            isInstructorManaged: function() {
                var topicType = this.get('type');
                return topicType === 'public_managed' || topicType === 'private_managed';
            },

            getMaxTeamSize: function(courseMaxTeamSize) {
                if (this.isInstructorManaged()) {
                    return null;
                }
                return this.get('max_team_size') || courseMaxTeamSize;
            }
        });
        return Topic;
    });
}).call(this, define || RequireJS.define);
