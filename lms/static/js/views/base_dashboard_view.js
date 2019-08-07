(function(define) {
    'use strict';
    define(['jquery', 'backbone'],
        function($, Backbone) {
            // This Base view is useful when eventing or other features are shared between two or more
            // views. Included with this view in the pubSub object allowing for events to be triggered
            // and shared with other views.
            var BaseDashboardView = Backbone.View.extend({
                pubSub: $.extend({}, Backbone.Events)
            });
            return BaseDashboardView;
        });
}).call(this, define || RequireJS.define);
