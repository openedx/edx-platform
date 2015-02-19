var edx = edx || {};

(function(Backbone, topicModel) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsCollection = Backbone.Collection.extend({
        model : topicModel
        //
        //parse: function(response) {
        //    //return response.discussions;
        //    return response.entries
        //}
    });
}).call(this, Backbone, edx.discussions.DiscussionTopicModel);
