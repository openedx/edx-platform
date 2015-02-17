var edx = edx || {};

(function(Backbone) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsModel = Backbone.Model.extend({
        defaults: {
            subcategories: '',
            entries: false
        }
    });
}).call(this, Backbone);
