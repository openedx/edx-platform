var edx = edx || {};

(function(Backbone) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsModel = Backbone.Model.extend({
        defaults: {
            subcategories: '',
            entries:''
        },
        parse: function(response){
            var attrs = $.extend(true, {}, response);

            _.each(attrs.entries, function(entry, entry_name) {
                entry.name = entry_name;
                entry.id = entry.id;
                entry.is_cohorted = entry.is_cohorted;
            });

            return attrs;

        }
    });
}).call(this, Backbone);
