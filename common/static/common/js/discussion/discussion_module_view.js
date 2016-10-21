/* globals Discussion, DiscussionUtil, DiscussionUser, DiscussionCourseSettings,  DiscussionThreadView, Content,
NewPostView */
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
        this.DiscussionModuleView = (function(_super) {
            __extends(DiscussionModuleView, _super);

            function DiscussionModuleView() {
                var self = this;
                this.navigateToPage = function() {
                    return DiscussionModuleView.prototype.navigateToPage.apply(self, arguments);
                };
                this.renderPagination = function() {
                    return DiscussionModuleView.prototype.renderPagination.apply(self, arguments);
                };
                this.addThread = function() {
                    return DiscussionModuleView.prototype.addThread.apply(self, arguments);
                };
                this.renderDiscussion = function() {
                    return DiscussionModuleView.prototype.renderDiscussion.apply(self, arguments);
                };
                this.loadPage = function() {
                    return DiscussionModuleView.prototype.loadPage.apply(self, arguments);
                };
                this.toggleDiscussion = function() {
                    return DiscussionModuleView.prototype.toggleDiscussion.apply(self, arguments);
                };
                this.hideDiscussion = function() {
                    return DiscussionModuleView.prototype.hideDiscussion.apply(self, arguments);
                };
                this.hideNewPost = function() {
                    return DiscussionModuleView.prototype.hideNewPost.apply(self, arguments);
                };
                this.toggleNewPost = function() {
                    return DiscussionModuleView.prototype.toggleNewPost.apply(self, arguments);
                };
                return DiscussionModuleView.__super__.constructor.apply(this, arguments);
            }

            DiscussionModuleView.prototype.events = {
                'click .discussion-show': 'toggleDiscussion',
                'keydown .discussion-show': function(event) {
                    return DiscussionUtil.activateOnSpace(event, this.toggleDiscussion);
                },
                'click .new-post-btn': 'toggleNewPost',
                'keydown .new-post-btn': function(event) {
                    return DiscussionUtil.activateOnSpace(event, this.toggleNewPost);
                },
                'click .discussion-paginator a': 'navigateToPage'
            };

            DiscussionModuleView.prototype.page_re = /\?discussion_page=(\d+)/;

            DiscussionModuleView.prototype.initialize = function(options) {
                var match;
                this.toggleDiscussionBtn = this.$('.discussion-show');
                match = this.page_re.exec(window.location.href);
                this.context = options.context || 'course';
                this.readOnly = $('.discussion-module').data('read-only');
                if (match) {
                    this.page = parseInt(match[1]);
                } else {
                    this.page = 1;
                }
            };

            DiscussionModuleView.prototype.toggleNewPost = function(event) {
                event.preventDefault();
                if (!this.newPostForm) {
                    this.toggleDiscussion();
                    this.isWaitingOnNewPost = true;
                    return;
                }
                if (this.showed) {
                    this.newPostForm.slideDown(300);
                } else {
                    this.newPostForm.show().focus();
                }
                this.toggleDiscussionBtn.addClass('shown');
                this.toggleDiscussionBtn.find('.button-text').html(gettext('Hide Discussion'));
                this.$('section.discussion').slideDown();
                this.showed = true;
            };

            DiscussionModuleView.prototype.hideNewPost = function() {
                return this.newPostForm.slideUp(300);
            };

            DiscussionModuleView.prototype.hideDiscussion = function() {
                this.$('section.discussion').slideUp();
                this.toggleDiscussionBtn.removeClass('shown');
                this.toggleDiscussionBtn.find('.button-text').html(gettext('Show Discussion'));
                this.showed = false;
            };

            DiscussionModuleView.prototype.toggleDiscussion = function() {
                var $elem,
                    self = this;
                if (this.showed) {
                    return this.hideDiscussion();
                } else {
                    this.toggleDiscussionBtn.addClass('shown');
                    this.toggleDiscussionBtn.find('.button-text').html(gettext('Hide Discussion'));
                    if (this.retrieved) {
                        this.$('section.discussion').slideDown();
                        this.showed = true;
                    } else {
                        $elem = this.toggleDiscussionBtn;
                        return this.loadPage($elem, function() {
                            self.hideDiscussion();
                            return DiscussionUtil.discussionAlert(
                                gettext('Sorry'),
                                gettext('We had some trouble loading the discussion. Please try again.')
                            );
                        });
                    }
                }
            };

            DiscussionModuleView.prototype.loadPage = function($elem, error) {
                var discussionId, url,
                    self = this;
                discussionId = this.$el.data('discussion-id');
                url = DiscussionUtil.urlFor('retrieve_discussion', discussionId) + ('?page=' + this.page);
                return DiscussionUtil.safeAjax({
                    $elem: $elem,
                    $loading: $elem,
                    takeFocus: true,
                    url: url,
                    type: 'GET',
                    dataType: 'json',
                    success: function(response, textStatus) {
                        return self.renderDiscussion($elem, response, textStatus, discussionId);
                    },
                    error: error
                });
            };

            DiscussionModuleView.prototype.renderDiscussion = function($elem, response, textStatus, discussionId) {
                var $discussion, user,
                    self = this;
                $elem.focus();
                user = new DiscussionUser(response.user_info);
                window.user = user;
                DiscussionUtil.setUser(user);
                Content.loadContentInfos(response.annotated_content_info);
                DiscussionUtil.loadRoles(response.roles);
                this.course_settings = new DiscussionCourseSettings(response.course_settings);
                this.discussion = new Discussion();
                this.discussion.reset(response.discussion_data, {
                    silent: false
                });
                $discussion = _.template($('#inline-discussion-template').html())({
                    'threads': response.discussion_data,
                    read_only: this.readOnly,
                    'discussionId': discussionId
                });
                if (this.$('section.discussion').length) {
                    this.$('section.discussion').replaceWith($discussion);
                } else {
                    this.$el.append($discussion);
                }
                this.newPostForm = this.$el.find('.new-post-article');
                this.threadviews = this.discussion.map(function(thread) {
                    var view;
                    view = new DiscussionThreadView({
                        el: self.$('article#thread_' + thread.id),
                        model: thread,
                        mode: 'inline',
                        context: self.context,
                        course_settings: self.course_settings,
                        topicId: discussionId
                    });
                    thread.on('thread:thread_type_updated', function() {
                        view.rerender();
                        return view.expand();
                    });
                    return view;
                });
                _.each(this.threadviews, function(dtv) {
                    return dtv.render();
                });
                DiscussionUtil.bulkUpdateContentInfo(window.$$annotated_content_info);
                this.newPostView = new NewPostView({
                    el: this.newPostForm,
                    collection: this.discussion,
                    course_settings: this.course_settings,
                    topicId: discussionId,
                    is_commentable_cohorted: response.is_commentable_cohorted
                });
                this.newPostView.render();
                this.listenTo(this.newPostView, 'newPost:cancel', this.hideNewPost);
                this.discussion.on('add', this.addThread);
                this.retrieved = true;
                this.showed = true;
                this.renderPagination(response.num_pages);
                if (this.isWaitingOnNewPost) {
                    return this.newPostForm.show().focus();
                }
            };

            DiscussionModuleView.prototype.addThread = function(thread) {
                var article, threadView;
                article = $("<article class='discussion-thread' id='thread_" + thread.id + "'></article>");
                this.$('section.discussion > .threads').prepend(article);
                threadView = new DiscussionThreadView({
                    el: article,
                    model: thread,
                    mode: 'inline',
                    context: this.context,
                    course_settings: this.course_settings,
                    topicId: this.$el.data('discussion-id')
                });
                threadView.render();
                return this.threadviews.unshift(threadView);
            };

            DiscussionModuleView.prototype.renderPagination = function(numPages) {
                var pageUrl, pagination, params;
                pageUrl = function(number) {
                    return '?discussion_page=' + number;
                };
                params = DiscussionUtil.getPaginationParams(this.page, numPages, pageUrl);
                pagination = _.template($('#pagination-template').html())(params);
                return this.$('section.discussion-pagination').html(pagination);
            };

            DiscussionModuleView.prototype.navigateToPage = function(event) {
                var currPage,
                    self = this;
                event.preventDefault();
                window.history.pushState({}, window.document.title, event.target.href);
                currPage = this.page;
                this.page = $(event.target).data('page-number');
                return this.loadPage($(event.target), function() {
                    self.page = currPage;
                    DiscussionUtil.discussionAlert(
                        gettext('Sorry'),
                        gettext('We had some trouble loading the threads you requested. Please try again.')
                    );
                });
            };

            return DiscussionModuleView;
        })(Backbone.View);
    }
}).call(window);
