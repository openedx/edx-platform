/* globals Thread, DiscussionUtil, Content */
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
        this.Discussion = (function(_super) {
            // eslint-disable-next-line no-use-before-define
            __extends(Discussion, _super);

            function Discussion() {
                return Discussion.__super__.constructor.apply(this, arguments);
            }

            Discussion.prototype.model = Thread;

            Discussion.prototype.initialize = function(models, options) {
                // eslint-disable-next-line no-var
                var self = this;
                if (!options) {
                    options = {};
                }
                this.pages = options.pages || 1;
                this.current_page = 1;
                this.sort_preference = options.sort;
                this.is_commentable_divided = options.is_commentable_divided;
                this.bind('add', function(item) {
                    item.discussion = self;
                });
                this.setSortComparator(this.sort_preference);
                return this.on('thread:remove', function(thread) {
                    self.remove(thread);
                });
            };

            Discussion.prototype.find = function(id) {
                // eslint-disable-next-line no-undef
                return _.first(this.where({
                    id: id
                }));
            };

            Discussion.prototype.hasMorePages = function() {
                return this.current_page < this.pages;
            };

            Discussion.prototype.setSortComparator = function(sortBy) {
                // eslint-disable-next-line default-case
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

            // eslint-disable-next-line consistent-return
            Discussion.prototype.addThread = function(thread) {
                // eslint-disable-next-line no-var
                var model;
                if (!this.find(thread.id)) {
                    model = new Thread(thread);
                    this.add(model);
                    return model;
                }
            };

            // eslint-disable-next-line camelcase
            Discussion.prototype.retrieveAnotherPage = function(mode, options, sort_options, error) {
                // eslint-disable-next-line no-var
                var data, url,
                    self = this;
                if (!options) {
                    options = {};
                }
                // eslint-disable-next-line camelcase
                if (!sort_options) {
                    // eslint-disable-next-line camelcase
                    sort_options = {};
                }
                data = {
                    page: this.current_page + 1
                };
                // eslint-disable-next-line no-undef
                if (_.contains(['unread', 'unanswered', 'flagged'], options.filter)) {
                    data[options.filter] = true;
                }
                // eslint-disable-next-line default-case
                switch (mode) {
                case 'search':
                    url = DiscussionUtil.urlFor('search');
                    data.text = options.search_text;
                    break;
                case 'commentables':
                    url = DiscussionUtil.urlFor('retrieve_discussion', options.commentable_ids);
                    data.commentable_ids = options.commentable_ids;
                    break;
                case 'all':
                    url = DiscussionUtil.urlFor('threads');
                    break;
                case 'followed':
                    url = DiscussionUtil.urlFor('followed_threads', options.user_id);
                    break;
                case 'user':
                    url = DiscussionUtil.urlFor('user_profile', options.user_id);
                    break;
                }
                if (options.group_id) {
                    data.group_id = options.group_id;
                }
                // eslint-disable-next-line camelcase
                data.sort_key = sort_options.sort_key || 'activity';
                // eslint-disable-next-line camelcase
                data.sort_order = sort_options.sort_order || 'desc';
                return DiscussionUtil.safeAjax({
                    $elem: this.$el,
                    url: url,
                    data: data,
                    dataType: 'json',
                    success: function(response) {
                        /* eslint-disable-next-line camelcase, no-var */
                        var models, new_collection, new_threads;
                        models = self.models;
                        // eslint-disable-next-line camelcase
                        new_threads = [
                            (function() {
                                // eslint-disable-next-line no-var
                                var _i, _len, _ref, _results;
                                _ref = response.discussion_data;
                                _results = [];
                                for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                                    data = _ref[_i];
                                    _results.push(new Thread(data));
                                }
                                return _results;
                            }())
                        ][0];
                        /* eslint-disable-next-line camelcase, no-undef */
                        new_collection = _.union(models, new_threads);
                        Content.loadContentInfos(response.annotated_content_info);
                        self.pages = response.num_pages;
                        self.current_page = response.page;
                        self.is_commentable_divided = response.is_commentable_divided;
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
                /* eslint-disable-next-line camelcase, no-var */
                var thread1_count, thread2_count;
                /* eslint-disable-next-line camelcase, radix */
                thread1_count = parseInt(thread1.get('votes').up_count);
                /* eslint-disable-next-line camelcase, radix */
                thread2_count = parseInt(thread2.get('votes').up_count);
                return this.pinnedThreadsSortComparatorWithCount(thread1, thread2, thread1_count, thread2_count);
            };

            Discussion.prototype.sortByComments = function(thread1, thread2) {
                /* eslint-disable-next-line camelcase, no-var */
                var thread1_count, thread2_count;
                /* eslint-disable-next-line camelcase, radix */
                thread1_count = parseInt(thread1.get('comments_count'));
                /* eslint-disable-next-line camelcase, radix */
                thread2_count = parseInt(thread2.get('comments_count'));
                return this.pinnedThreadsSortComparatorWithCount(thread1, thread2, thread1_count, thread2_count);
            };

            Discussion.prototype.pinnedThreadsSortComparatorWithCount = function(
                // eslint-disable-next-line camelcase
                thread1, thread2, thread1_count, thread2_count
            ) {
                if (thread1.get('pinned') && !thread2.get('pinned')) {
                    return -1;
                } else if (thread2.get('pinned') && !thread1.get('pinned')) {
                    return 1;
                } else {
                    // eslint-disable-next-line camelcase
                    if (thread1_count > thread2_count) {
                        return -1;
                    // eslint-disable-next-line camelcase
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
                // eslint-disable-next-line no-var
                var preferredDate, threadLastActivityAtTime, today;
                threadLastActivityAtTime = new Date(thread.get('last_activity_at')).getTime();
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
        // eslint-disable-next-line no-undef
        }(Backbone.Collection));
    }
}).call(window);
