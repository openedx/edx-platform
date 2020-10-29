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
                type: 'open'
            },

            initialize: function(options) {
                this.url = options.url;
            },

            isInstructorManaged: function() {
                var topicType = this.get('type');
                return topicType === 'public_managed' || topicType === 'private_managed';
            }
        });
        return Topic;
    });
}).call(this, define || RequireJS.define);
