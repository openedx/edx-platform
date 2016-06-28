/* globals Thread, DiscussionUtil, Content */
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

    if (typeof Backbone !== "undefined" && Backbone !== null) {
        this.Discussion = (function(_super) {

            __extends(Discussion, _super);

            function Discussion() {
                return Discussion.__super__.constructor.apply(this, arguments);
            }

            Discussion.prototype.model = Thread;

            Discussion.prototype.initialize = function(models, options) {
                var self = this;
                if (!options) {
                    options = {};
                }
                this.pages = options.pages || 1;
                this.current_page = 1;
                this.sort_preference = options.sort;
                this.bind("add", function(item) {
                    item.discussion = self;
                });
                this.setSortComparator(this.sort_preference);
                return this.on("thread:remove", function(thread) {
                    self.remove(thread);
                });
            };

            Discussion.prototype.find = function(id) {
                return _.first(this.where({
                    id: id
                }));
            };

            Discussion.prototype.hasMorePages = function() {
                return this.current_page < this.pages;
            };

            Discussion.prototype.setSortComparator = function(sortBy) {
                switch (sortBy) {
                    case 'activity':
                        this.comparator = this.sortByDateRecentFirst;
                        break;
                    case 'votes':
                        this.comparator = this.sortByVotes;
                        break;
                    case 'comments':
                        this.comparator = this.sortByComments;
                        break;
                }
            };

            Discussion.prototype.addThread = function(thread) {
                var model;
                if (!this.find(thread.id)) {
                    model = new Thread(thread);
                    this.add(model);
                    return model;
                }
            };

            Discussion.prototype.retrieveAnotherPage = function(mode, options, sort_options, error) {
                var data, url,
                    self = this;
                if (!options) {
                    options = {};
                }
                if (!sort_options) {
                    sort_options = {};
                }
                data = {
                    page: this.current_page + 1
                };
                if (_.contains(["unread", "unanswered", "flagged"], options.filter)) {
                    data[options.filter] = true;
                }
                switch (mode) {
                    case 'search':
                        url = DiscussionUtil.urlFor('search');
                        data.text = options.search_text;
                        break;
                    case 'commentables':
                        url = DiscussionUtil.urlFor('search');
                        data.commentable_ids = options.commentable_ids;
                        break;
                    case 'all':
                        url = DiscussionUtil.urlFor('threads');
                        break;
                    case 'followed':
                        url = DiscussionUtil.urlFor('followed_threads', options.user_id);
                }
                if (options.group_id) {
                    data.group_id = options.group_id;
                }
                data.sort_key = sort_options.sort_key || 'activity';
                data.sort_order = sort_options.sort_order || 'desc';
                return DiscussionUtil.safeAjax({
                    $elem: this.$el,
                    url: url,
                    data: data,
                    dataType: 'json',
                    success: function(response) {
                        var models, new_collection, new_threads;
                        models = self.models;
                        new_threads = [
                            (function() {
                                var _i, _len, _ref, _results;
                                _ref = response.discussion_data;
                                _results = [];
                                for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                                    data = _ref[_i];
                                    _results.push(new Thread(data));
                                }
                                return _results;
                            })()
                        ][0];
                        new_collection = _.union(models, new_threads);
                        Content.loadContentInfos(response.annotated_content_info);
                        self.pages = response.num_pages;
                        self.current_page = response.page;
                        return self.reset(new_collection);
                    },
                    error: error
                });
            };

            Discussion.prototype.sortByDate = function(thread) {
                /*
                 The comment client asks each thread for a value by which to sort the collection
                 and calls this sort routine regardless of the order returned from the LMS/comments service
                 so, this takes advantage of this per-thread value and returns tomorrow's date
                 for pinned threads, ensuring that they appear first, (which is the intent of pinned threads)
                 */
                return this.pinnedThreadsSortComparatorWithDate(thread, true);
            };

            Discussion.prototype.sortByDateRecentFirst = function(thread) {
                /*
                 Same as above
                 but negative to flip the order (newest first)
                 */
                return this.pinnedThreadsSortComparatorWithDate(thread, false);
            };

            Discussion.prototype.sortByVotes = function(thread1, thread2) {
                var thread1_count, thread2_count;
                thread1_count = parseInt(thread1.get("votes").up_count);
                thread2_count = parseInt(thread2.get("votes").up_count);
                return this.pinnedThreadsSortComparatorWithCount(thread1, thread2, thread1_count, thread2_count);
            };

            Discussion.prototype.sortByComments = function(thread1, thread2) {
                var thread1_count, thread2_count;
                thread1_count = parseInt(thread1.get("comments_count"));
                thread2_count = parseInt(thread2.get("comments_count"));
                return this.pinnedThreadsSortComparatorWithCount(thread1, thread2, thread1_count, thread2_count);
            };

            Discussion.prototype.pinnedThreadsSortComparatorWithCount = function(
                thread1, thread2, thread1_count, thread2_count
            ) {
                if (thread1.get('pinned') && !thread2.get('pinned')) {
                    return -1;
                } else if (thread2.get('pinned') && !thread1.get('pinned')) {
                    return 1;
                } else {
                    if (thread1_count > thread2_count) {
                        return -1;
                    } else if (thread2_count > thread1_count) {
                        return 1;
                    } else {
                        if (thread1.created_at_time() > thread2.created_at_time()) {
                            return -1;
                        } else {
                            return 1;
                        }
                    }
                }
            };

            Discussion.prototype.pinnedThreadsSortComparatorWithDate = function(thread, ascending) {
                var preferredDate, threadLastActivityAtTime, today;
                threadLastActivityAtTime = new Date(thread.get("last_activity_at")).getTime();
                if (thread.get('pinned')) {
                    today = new Date();
                    preferredDate = new Date(today.getTime() + (24 * 60 * 60 * 1000) + threadLastActivityAtTime);
                } else {
                    preferredDate = threadLastActivityAtTime;
                }
                if (ascending) {
                    return preferredDate;
                } else {
                    return -preferredDate;
                }
            };

            return Discussion;

        })(Backbone.Collection);
    }

}).call(window);
