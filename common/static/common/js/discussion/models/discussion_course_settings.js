(function() {
    'use strict';
    var __hasProp = {}.hasOwnProperty,
        __extends = function(child, parent) {
            for (var key in parent) {
                if (__hasProp.call(parent, key)) {
                    child[key] = parent[key];
                }
            }
            function ctor() {
                this.constructor = child;
            }

            ctor.prototype = parent.prototype;
            child.prototype = new ctor();
            child.__super__ = parent.prototype;
            return child;
        };

    if (typeof Backbone !== 'undefined' && Backbone !== null) {
        this.DiscussionCourseSettings = (function(_super) {
            __extends(DiscussionCourseSettings, _super);

            function DiscussionCourseSettings() {
                return DiscussionCourseSettings.__super__.constructor.apply(this, arguments);
            }

            return DiscussionCourseSettings;
        })(Backbone.Model);
    }
}).call(this);
