(function() {
    'use strict';

    // eslint-disable-next-line no-var
    var __hasProp = {}.hasOwnProperty,
        __extends = function(child, parent) {
            // eslint-disable-next-line no-var
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

    // eslint-disable-next-line no-undef
    if (typeof Backbone !== 'undefined' && Backbone !== null) {
        this.DiscussionCourseSettings = (function(_super) {
            // eslint-disable-next-line no-use-before-define
            __extends(DiscussionCourseSettings, _super);

            function DiscussionCourseSettings() {
                return DiscussionCourseSettings.__super__.constructor.apply(this, arguments);
            }

            return DiscussionCourseSettings;
        // eslint-disable-next-line no-undef
        }(Backbone.Model));
    }
}).call(this);
