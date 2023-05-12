/**
 * Model for a topic.
 */
(function(define) {
    'use strict';

    define(['backbone'], function(Backbone) {
        // eslint-disable-next-line no-var
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
                // eslint-disable-next-line no-var
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
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
