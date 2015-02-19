var edx = edx || {};

(function(Backbone, topicCollection) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsModel = Backbone.Model.extend({
        defaults: {
            subcategories: '',
            entries:new topicCollection([])
        },
        parse: function(response){
            var attrs = $.extend(true, {}, response);

            _.each(attrs.entries, function(entry, entry_name) {
                entry.name = entry_name;
            });

            return attrs;
        }
    });
}).call(this, Backbone, edx.discussions.DiscussionTopicsCollection);
