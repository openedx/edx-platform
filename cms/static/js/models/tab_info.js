define(["backbone"], function(Backbone) {
    /**
     * Simple model for an editor tab
     */
    'use strict';
    var TabInfo = Backbone.Model.extend({
        defaults: {
            display_name: ""
        }
    });
    return TabInfo;
});
