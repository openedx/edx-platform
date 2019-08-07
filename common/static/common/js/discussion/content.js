/* globals DiscussionUtil, Comments */
(function() {
    'use strict';

    var __hasProp = {}.hasOwnProperty;

    function __extends(child, parent) {
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
    }

    var __indexOf = [].indexOf || function(item) {
        for (var i = 0, l = this.length; i < l; i++) {
            if (i in this && this[i] === item) {
                return i;
            }
        }
        return -1;
    };

    if (typeof Backbone !== 'undefined' && Backbone !== null) {
        this.Content = (function(_super) {
            __extends(Content, _super);

            function Content() {
                return Content.__super__.constructor.apply(this, arguments);
            }

            Content.contents = {};

            Content.contentInfos = {};

            Content.prototype.template = function() {
                return DiscussionUtil.getTemplate('_content');
            };

            Content.prototype.actions = {
                editable: '.admin-edit',
                can_reply: '.discussion-reply',
                can_delete: '.admin-delete',
                can_openclose: '.admin-openclose',
                can_report: '.admin-report',
                can_vote: '.admin-vote'
            };

            Content.prototype.urlMappers = {};

            Content.prototype.urlFor = function(name) {
                return this.urlMappers[name].apply(this);
            };

            Content.prototype.can = function(action) {
                return (this.get('ability') || {})[action];
            };

            Content.prototype.canBeEndorsed = function() {
                return false;
            };

            Content.prototype.updateInfo = function(info) {
                if (info) {
                    this.set('ability', info.ability);
                    this.set('voted', info.voted);
                    return this.set('subscribed', info.subscribed);
                }
            };

            Content.prototype.addComment = function(comment, options) {
                var comments_count, model, thread;
                options = (options) || {};
                if (!options.silent) {
                    thread = this.get('thread');
                    comments_count = parseInt(thread.get('comments_count'));
                    thread.set('comments_count', comments_count + 1);
                }
                this.get('children').push(comment);
                model = new Comment($.extend({}, comment, {
                    thread: this.get('thread')
                }));
                this.get('comments').add(model);
                this.trigger('comment:add');
                return model;
            };

            Content.prototype.removeComment = function(comment) {
                var comments_count, thread;
                thread = this.get('thread');
                comments_count = parseInt(thread.get('comments_count'));
                thread.set('comments_count', comments_count - 1 - comment.getCommentsCount());
                return this.trigger('comment:remove');
            };

            Content.prototype.resetComments = function(children) {
                var comment, _i, _len, _ref, _results;
                this.set('children', []);
                this.set('comments', new Comments());
                _ref = children || [];
                _results = [];
                for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                    comment = _ref[_i];
                    _results.push(this.addComment(comment, {
                        silent: true
                    }));
                }
                return _results;
            };

            Content.prototype.initialize = function() {
                var userId;
                Content.addContent(this.id, this);
                userId = this.get('user_id');
                if (userId) {
                    this.set('staff_authored', DiscussionUtil.isStaff(userId));
                    this.set('community_ta_authored', DiscussionUtil.isTA(userId) || DiscussionUtil.isGroupTA(userId));
                } else {
                    this.set('staff_authored', false);
                    this.set('community_ta_authored', false);
                }
                if (Content.getInfo(this.id)) {
                    this.updateInfo(Content.getInfo(this.id));
                }
                this.set('user_url', DiscussionUtil.urlFor('user_profile', userId));
                return this.resetComments(this.get('children'));
            };

            Content.prototype.remove = function() {
                if (this.get('type') === 'comment') {
                    this.get('thread').removeComment(this);
                    return this.get('thread').trigger('comment:remove', this);
                } else {
                    return this.trigger('thread:remove', this);
                }
            };

            Content.addContent = function(id, content) {
                this.contents[id] = content;
            };

            Content.getContent = function(id) {
                return this.contents[id];
            };

            Content.getInfo = function(id) {
                return this.contentInfos[id];
            };

            Content.loadContentInfos = function(infos) {
                var id, info;
                for (id in infos) {
                    if (infos.hasOwnProperty(id)) {
                        info = infos[id];
                        if (this.getContent(id)) {
                            this.getContent(id).updateInfo(info);
                        }
                    }
                }
                return $.extend(this.contentInfos, infos);
            };

            Content.prototype.pinThread = function() {
                var pinned;
                pinned = this.get('pinned');
                this.set('pinned', pinned);
                return this.trigger('change', this);
            };

            Content.prototype.unPinThread = function() {
                var pinned;
                pinned = this.get('pinned');
                this.set('pinned', pinned);
                return this.trigger('change', this);
            };

            Content.prototype.flagAbuse = function() {
                var temp_array;
                temp_array = this.get('abuse_flaggers');
                temp_array.push(window.user.get('id'));
                this.set('abuse_flaggers', temp_array);
                return this.trigger('change', this);
            };

            Content.prototype.unflagAbuse = function() {
                this.get('abuse_flaggers').pop(window.user.get('id'));
                return this.trigger('change', this);
            };

            Content.prototype.isFlagged = function() {
                var flaggers, user;
                user = DiscussionUtil.getUser();
                flaggers = this.get('abuse_flaggers');
                return user && (
                    (__indexOf.call(flaggers, user.id) >= 0) ||
                    (DiscussionUtil.isPrivilegedUser(user.id) && flaggers.length > 0)
                );
            };

            Content.prototype.incrementVote = function(increment) {
                var newVotes;
                newVotes = _.clone(this.get('votes'));
                newVotes.up_count = newVotes.up_count + increment;
                return this.set('votes', newVotes);
            };

            Content.prototype.vote = function() {
                return this.incrementVote(1);
            };

            Content.prototype.unvote = function() {
                return this.incrementVote(-1);
            };

            return Content;
        }(Backbone.Model));
        this.Thread = (function(_super) {
            __extends(Thread, _super);

            function Thread() {
                return Thread.__super__.constructor.apply(this, arguments);
            }

            Thread.prototype.urlMappers = {
                retrieve: function() {
                    return DiscussionUtil.urlFor('retrieve_single_thread', this.get('commentable_id'), this.id);
                },
                reply: function() {
                    return DiscussionUtil.urlFor('create_comment', this.id);
                },
                unvote: function() {
                    return DiscussionUtil.urlFor('undo_vote_for_' + (this.get('type')), this.id);
                },
                upvote: function() {
                    return DiscussionUtil.urlFor('upvote_' + (this.get('type')), this.id);
                },
                downvote: function() {
                    return DiscussionUtil.urlFor('downvote_' + (this.get('type')), this.id);
                },
                close: function() {
                    return DiscussionUtil.urlFor('openclose_thread', this.id);
                },
                update: function() {
                    return DiscussionUtil.urlFor('update_thread', this.id);
                },
                _delete: function() {
                    return DiscussionUtil.urlFor('delete_thread', this.id);
                },
                follow: function() {
                    return DiscussionUtil.urlFor('follow_thread', this.id);
                },
                unfollow: function() {
                    return DiscussionUtil.urlFor('unfollow_thread', this.id);
                },
                flagAbuse: function() {
                    return DiscussionUtil.urlFor('flagAbuse_' + (this.get('type')), this.id);
                },
                unFlagAbuse: function() {
                    return DiscussionUtil.urlFor('unFlagAbuse_' + (this.get('type')), this.id);
                },
                pinThread: function() {
                    return DiscussionUtil.urlFor('pin_thread', this.id);
                },
                unPinThread: function() {
                    return DiscussionUtil.urlFor('un_pin_thread', this.id);
                }
            };

            Thread.prototype.initialize = function() {
                this.set('thread', this);
                return Thread.__super__.initialize.call(this);
            };

            Thread.prototype.comment = function() {
                return this.set('comments_count', parseInt(this.get('comments_count')) + 1);
            };

            Thread.prototype.follow = function() {
                return this.set('subscribed', true);
            };

            Thread.prototype.unfollow = function() {
                return this.set('subscribed', false);
            };

            Thread.prototype.display_body = function() {
                if (this.has('highlighted_body')) {
                    return String(this.get('highlighted_body'))
                        .replace(/<highlight>/g, '<mark>')
                        .replace(/<\/highlight>/g, '</mark>');
                } else {
                    return this.get('body');
                }
            };

            Thread.prototype.display_title = function() {
                if (this.has('highlighted_title')) {
                    return String(this.get('highlighted_title'))
                        .replace(/<highlight>/g, '<mark>')
                        .replace(/<\/highlight>/g, '</mark>');
                } else {
                    return this.get('title');
                }
            };

            Thread.prototype.toJSON = function() {
                var json_attributes;
                json_attributes = _.clone(this.attributes);
                return _.extend(json_attributes, {
                    title: this.display_title(),
                    body: this.display_body()
                });
            };

            Thread.prototype.created_at_date = function() {
                return new Date(this.get('created_at'));
            };

            Thread.prototype.created_at_time = function() {
                return new Date(this.get('created_at')).getTime();
            };

            Thread.prototype.hasResponses = function() {
                return this.get('comments_count') > 0;
            };

            return Thread;
        }(this.Content));
        this.Comment = (function(_super) {
            __extends(Comment, _super);

            function Comment() {
                var self = this;
                this.canBeEndorsed = function() {
                    return Comment.prototype.canBeEndorsed.apply(self, arguments);
                };
                return Comment.__super__.constructor.apply(this, arguments);
            }

            Comment.prototype.urlMappers = {
                reply: function() {
                    return DiscussionUtil.urlFor('create_sub_comment', this.id);
                },
                unvote: function() {
                    return DiscussionUtil.urlFor('undo_vote_for_' + (this.get('type')), this.id);
                },
                upvote: function() {
                    return DiscussionUtil.urlFor('upvote_' + (this.get('type')), this.id);
                },
                downvote: function() {
                    return DiscussionUtil.urlFor('downvote_' + (this.get('type')), this.id);
                },
                endorse: function() {
                    return DiscussionUtil.urlFor('endorse_comment', this.id);
                },
                update: function() {
                    return DiscussionUtil.urlFor('update_comment', this.id);
                },
                _delete: function() {
                    return DiscussionUtil.urlFor('delete_comment', this.id);
                },
                flagAbuse: function() {
                    return DiscussionUtil.urlFor('flagAbuse_' + (this.get('type')), this.id);
                },
                unFlagAbuse: function() {
                    return DiscussionUtil.urlFor('unFlagAbuse_' + (this.get('type')), this.id);
                }
            };

            Comment.prototype.getCommentsCount = function() {
                var count;
                count = 0;
                this.get('comments').each(function(comment) {
                    return count += comment.getCommentsCount() + 1;
                });
                return count;
            };

            Comment.prototype.canBeEndorsed = function() {
                var user_id;
                user_id = window.user.get('id');
                return user_id && (
                    DiscussionUtil.isPrivilegedUser(user_id) ||
                    (
                        this.get('thread').get('thread_type') === 'question' &&
                        this.get('thread').get('user_id') === user_id
                    )
                );
            };

            return Comment;
        }(this.Content));

        this.Comments = (function(_super) {
            __extends(Comments, _super);

            function Comments() {
                return Comments.__super__.constructor.apply(this, arguments);
            }

            Comments.prototype.model = Comment;

            Comments.prototype.initialize = function() {
                var self = this;
                return this.bind('add', function(item) {
                    item.collection = self;
                });
            };

            Comments.prototype.find = function(id) {
                return _.first(this.where({
                    id: id
                }));
            };

            return Comments;
        }(Backbone.Collection));
    }
}).call(window);
