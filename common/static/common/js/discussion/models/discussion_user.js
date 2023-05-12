(function() {
    'use strict';

    // eslint-disable-next-line no-var
    var __hasProp = {}.hasOwnProperty,
        __extends = function(child, parent) {
            /* eslint-disable-next-line no-var, no-restricted-syntax */
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
        this.DiscussionUser = (function(_super) {
            // eslint-disable-next-line no-use-before-define
            __extends(DiscussionUser, _super);

            function DiscussionUser() {
                return DiscussionUser.__super__.constructor.apply(this, arguments);
            }

            DiscussionUser.prototype.following = function(thread) {
                // eslint-disable-next-line no-undef
                return _.include(this.get('subscribed_thread_ids'), thread.id);
            };

            DiscussionUser.prototype.voted = function(thread) {
                // eslint-disable-next-line no-undef
                return _.include(this.get('upvoted_ids'), thread.id);
            };

            DiscussionUser.prototype.vote = function(thread) {
                this.get('upvoted_ids').push(thread.id);
                return thread.vote();
            };

            DiscussionUser.prototype.unvote = function(thread) {
                // eslint-disable-next-line no-undef
                this.set('upvoted_ids', _.without(this.get('upvoted_ids'), thread.id));
                return thread.unvote();
            };

            return DiscussionUser;
        // eslint-disable-next-line no-undef
        }(Backbone.Model));
    }
}).call(this);
