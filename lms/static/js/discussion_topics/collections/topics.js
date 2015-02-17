var edx = edx || {};

(function(Backbone, DiscussionTopicModel) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsCollection = Backbone.Collection.extend({
        model : DiscussionTopicModel,
        comparator: "name",

        parse: function(response) {
            //return response.discussions;
            return response.entries
        }
    });
}).call(this, Backbone, edx.discussions.DiscussionTopicsCollection);
