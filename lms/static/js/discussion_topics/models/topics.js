var edx = edx || {};

(function(Backbone, topicCollection) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsModel = Backbone.Model.extend({
        defaults: {
            subcategories: '',
            entries: []
        },
        parse: function(response) {
            var attrs = $.extend(true, {}, response),
                entriesList = [];

            _.each(attrs.entries, function(entry, entry_name) {
                entry.name = entry_name;
                entriesList.push(entry);
            });

            attrs.entries = new topicCollection(entriesList);
            return attrs;
        }
    });
}).call(this, Backbone, edx.discussions.DiscussionTopicsCollection);
