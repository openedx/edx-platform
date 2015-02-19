var edx = edx || {};

(function(Backbone) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicModel = Backbone.Model.extend({
        idAttribute: 'id',
        defaults: {
            id:0,
            name: '',
            is_cohorted: false
        }
    });
}).call(this, Backbone);
