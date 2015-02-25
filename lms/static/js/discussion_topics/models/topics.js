var edx = edx || {};

(function(Backbone, topicCollection) {
    'use strict';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsModel = Backbone.Model.extend({
        //defaults: function() {
        //    return {
        //        subcategories: '',
        //        entries: [],
        //        children:[]
        //    };
        //},

        //parse: function(response) {
        //    var attrs = $.extend(true, {}, response),
        //        entriesList = [];
        //
        //    var makeInlineCategories = function(that, subcategories) {
        //         _.each(subcategories, function(subcategory, name) {
        //            subcategory.name=name;
        //            subcategory.allCohorted=false;
        //             subcategory = new edx.discussions.DiscussionTopicsModel(subcategory);
        //             if (!subcategories) {
        //                return;
        //            }
        //            return makeInlineCategories(that, subcategory.get('subcategories'));
        //        });
        //    };
        //    makeInlineCategories(this, attrs.subcategories);
        //
        //    _.each(attrs.entries, function(entry, entry_name) {
        //        entry.name = entry_name;
        //        entriesList.push(entry);
        //    });
        //
        //    attrs.entries = new topicCollection(entriesList);
        //    return attrs;
        //}
    });
}).call(this, Backbone, edx.discussions.DiscussionTopicsCollection);
