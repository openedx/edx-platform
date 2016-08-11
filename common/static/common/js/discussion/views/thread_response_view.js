/* globals
    Comments, ResponseCommentView, DiscussionUtil, ThreadResponseEditView,
    ThreadResponseShowView, DiscussionContentView
*/
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
        this.ThreadResponseView = (function(_super) {
            __extends(ThreadResponseView, _super);

            function ThreadResponseView() {
                var self = this;
                this.update = function() {
                    return ThreadResponseView.prototype.update.apply(self, arguments);
                };
                this.edit = function() {
                    return ThreadResponseView.prototype.edit.apply(self, arguments);
                };
                this.cancelEdit = function() {
                    return ThreadResponseView.prototype.cancelEdit.apply(self, arguments);
                };
                this._delete = function() {
                    return ThreadResponseView.prototype._delete.apply(self, arguments);
                };
                this.renderComment = function() {
                    return ThreadResponseView.prototype.renderComment.apply(self, arguments);
                };
                return ThreadResponseView.__super__.constructor.apply(this, arguments);
            }

            ThreadResponseView.prototype.tagName = 'li';

            ThreadResponseView.prototype.className = 'forum-response';

            ThreadResponseView.prototype.events = {
                'click .discussion-submit-comment': 'submitComment',
                'focus .wmd-input': 'showEditorChrome'
            };

            ThreadResponseView.prototype.$ = function(selector) {
                return this.$el.find(selector);
            };

            ThreadResponseView.prototype.initialize = function(options) {
                this.collapseComments = options.collapseComments;
                this.createShowView();
                this.readOnly = $('.discussion-module').data('read-only');
            };

            ThreadResponseView.prototype.renderTemplate = function() {
                var container, templateData, _ref;
                this.template = _.template($('#thread-response-template').html());
                container = $('#discussion-container');
                if (!container.length) {
                    container = $('.discussion-module');
                }
                templateData = _.extend(this.model.toJSON(), {
                    wmdId: (_ref = this.model.id) !== null ? _ref : (new Date()).getTime(),
                    create_sub_comment: container.data('user-create-subcomment'),
                    readOnly: this.readOnly
                });
                return this.template(templateData);
            };

            ThreadResponseView.prototype.render = function() {
                this.$el.addClass('response_' + this.model.get('id'));
                this.$el.html(this.renderTemplate());
                this.delegateEvents();
                this.renderShowView();
                this.renderAttrs();
                if (this.model.get('thread').get('closed')) {
                    this.hideCommentForm();
                }
                this.renderComments();
                return this;
            };

            ThreadResponseView.prototype.afterInsert = function() {
                this.makeWmdEditor('comment-body');
                return this.hideEditorChrome();
            };

            ThreadResponseView.prototype.hideEditorChrome = function() {
                this.$('.wmd-button-row').hide();
                this.$('.wmd-preview-container').hide();
                this.$('.wmd-input').css({
                    height: '35px',
                    padding: '5px'
                });
                return this.$('.comment-post-control').hide();
            };

            ThreadResponseView.prototype.showEditorChrome = function() {
                this.$('.wmd-button-row').show();
                this.$('.wmd-preview-container').show();
                this.$('.comment-post-control').show();
                return this.$('.wmd-input').css({
                    height: '125px',
                    padding: '10px'
                });
            };

            ThreadResponseView.prototype.renderComments = function() {
                var collectComments, comments,
                    self = this;
                comments = new Comments();
                this.commentViews = [];
                comments.comparator = function(comment) {
                    return comment.get('created_at');
                };
                collectComments = function(comment) {
                    var children;
                    comments.add(comment);
                    children = new Comments(comment.get('children'));
                    return children.each(function(child) {
                        child.parent = comment;
                        return collectComments(child);
                    });
                };
                this.model.get('comments').each(collectComments);
                comments.each(function(comment) {
                    return self.renderComment(comment, false, null);
                });
                if (this.collapseComments && comments.length) {
                    this.$('.comments').hide();
                    return this.$('.action-show-comments').on('click', function(event) {
                        event.preventDefault();
                        self.$('.action-show-comments').hide();
                        return self.$('.comments').show();
                    });
                } else {
                    return this.$('.action-show-comments').hide();
                }
            };

            ThreadResponseView.prototype.renderComment = function(comment) {
                var view,
                    self = this;
                comment.set('thread', this.model.get('thread'));
                view = new ResponseCommentView({
                    model: comment
                });
                view.render();
                if (this.readOnly) {
                    this.$el.find('.comments').append(view.el);
                } else {
                    this.$el.find('.comments .new-comment').before(view.el);
                }
                view.bind('comment:edit', function(event) {
                    if (self.editView) {
                        self.cancelEdit(event);
                    }
                    self.cancelCommentEdits();
                    return self.hideCommentForm();
                });
                view.bind('comment:cancel_edit', function() {
                    return self.showCommentForm();
                });
                this.commentViews.push(view);
                return view;
            };

            ThreadResponseView.prototype.submitComment = function(event) {
                var body, comment, url, view;
                event.preventDefault();
                url = this.model.urlFor('reply');
                body = this.getWmdContent('comment-body');
                if (!body.trim().length) {
                    return;
                }
                this.setWmdContent('comment-body', '');
                comment = new Comment({
                    body: body,
                    created_at: (new Date()).toISOString(),
                    username: window.user.get('username'),
                    abuse_flaggers: [],
                    user_id: window.user.get('id'),
                    id: 'unsaved'
                });
                view = this.renderComment(comment);
                this.hideEditorChrome();
                this.trigger('comment:add', comment);
                return DiscussionUtil.safeAjax({
                    $elem: $(event.target),
                    url: url,
                    type: 'POST',
                    dataType: 'json',
                    data: {
                        body: body
                    },
                    success: function(response) {
                        comment.set(response.content);
                        comment.updateInfo(response.annotated_content_info);
                        return view.render();
                    }
                });
            };

            ThreadResponseView.prototype._delete = function(event) {
                var $elem, url;
                event.preventDefault();
                if (!this.model.can('can_delete')) {
                    return;
                }
                if (!confirm(gettext('Are you sure you want to delete this response?'))) {
                    return;
                }
                url = this.model.urlFor('_delete');
                this.model.remove();
                this.$el.remove();
                $elem = $(event.target);
                return DiscussionUtil.safeAjax({
                    $elem: $elem,
                    url: url,
                    type: 'POST'
                });
            };

            ThreadResponseView.prototype.createEditView = function() {
                if (this.showView) {
                    this.showView.$el.empty();
                }
                if (this.editView) {
                    this.editView.model = this.model;
                } else {
                    this.editView = new ThreadResponseEditView({
                        model: this.model
                    });
                    this.editView.bind('response:update', this.update);
                    return this.editView.bind('response:cancel_edit', this.cancelEdit);
                }
            };

            ThreadResponseView.prototype.renderSubView = function(view) {
                view.setElement(this.$('.discussion-response'));
                view.render();
                return view.delegateEvents();
            };

            ThreadResponseView.prototype.renderEditView = function() {
                return this.renderSubView(this.editView);
            };

            ThreadResponseView.prototype.cancelCommentEdits = function() {
                return _.each(this.commentViews, function(view) {
                    return view.cancelEdit();
                });
            };

            ThreadResponseView.prototype.hideCommentForm = function() {
                return this.$('.comment-form').closest('li').hide();
            };

            ThreadResponseView.prototype.showCommentForm = function() {
                return this.$('.comment-form').closest('li').show();
            };

            ThreadResponseView.prototype.createShowView = function() {
                var self = this;

                if (this.editView) {
                    this.editView.$el.empty();
                }
                if (this.showView) {
                    this.showView.model = this.model;
                } else {
                    this.showView = new ThreadResponseShowView({
                        model: this.model
                    });
                    this.showView.bind('response:_delete', this._delete);
                    this.showView.bind('response:edit', this.edit);
                    return this.showView.on('comment:endorse', function() {
                        return self.trigger('comment:endorse');
                    });
                }
            };

            ThreadResponseView.prototype.renderShowView = function() {
                return this.renderSubView(this.showView);
            };

            ThreadResponseView.prototype.cancelEdit = function(event) {
                event.preventDefault();
                this.createShowView();
                this.renderShowView();
                return this.showCommentForm();
            };

            ThreadResponseView.prototype.edit = function() {
                this.createEditView();
                this.renderEditView();
                this.cancelCommentEdits();
                return this.hideCommentForm();
            };

            ThreadResponseView.prototype.update = function(event) {
                var newBody, url,
                    self = this;
                newBody = this.editView.$('.edit-post-body textarea').val();
                url = DiscussionUtil.urlFor('update_comment', this.model.id);
                return DiscussionUtil.safeAjax({
                    $elem: $(event.target),
                    $loading: event ? $(event.target) : void 0,
                    url: url,
                    type: 'POST',
                    dataType: 'json',
                    data: {
                        body: newBody
                    },
                    error: DiscussionUtil.formErrorHandler(this.$('.edit-post-form-errors')),
                    success: function() {
                        self.editView.$('.edit-post-body textarea').val('').attr('prev-text', '');
                        self.editView.$('.wmd-preview p').html('');
                        self.model.set({
                            body: newBody
                        });
                        self.createShowView();
                        self.renderShowView();
                        return self.showCommentForm();
                    }
                });
            };

            return ThreadResponseView;
        })(DiscussionContentView);
    }
}).call(window);
