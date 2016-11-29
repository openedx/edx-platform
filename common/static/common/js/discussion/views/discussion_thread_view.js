/* globals
    Comments, Content, DiscussionContentView, DiscussionThreadEditView,
    DiscussionThreadShowView, DiscussionUtil, ThreadResponseView
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
        this.DiscussionThreadView = (function(_super) {
            var INITIAL_RESPONSE_PAGE_SIZE, SUBSEQUENT_RESPONSE_PAGE_SIZE;

            __extends(DiscussionThreadView, _super);

            function DiscussionThreadView() {
                var self = this;
                this._delete = function() {
                    return DiscussionThreadView.prototype._delete.apply(self, arguments);
                };
                this.closeEditView = function() {
                    return DiscussionThreadView.prototype.closeEditView.apply(self, arguments);
                };
                this.edit = function() {
                    return DiscussionThreadView.prototype.edit.apply(self, arguments);
                };
                this.endorseThread = function() {
                    return DiscussionThreadView.prototype.endorseThread.apply(self, arguments);
                };
                this.addComment = function() {
                    return DiscussionThreadView.prototype.addComment.apply(self, arguments);
                };
                this.renderAddResponseButton = function() {
                    return DiscussionThreadView.prototype.renderAddResponseButton.apply(self, arguments);
                };
                this.renderResponseToList = function() {
                    return DiscussionThreadView.prototype.renderResponseToList.apply(self, arguments);
                };
                this.renderResponseCountAndPagination = function() {
                    return DiscussionThreadView.prototype.renderResponseCountAndPagination.apply(self, arguments);
                };
                return DiscussionThreadView.__super__.constructor.apply(this, arguments);
            }

            INITIAL_RESPONSE_PAGE_SIZE = 25;

            SUBSEQUENT_RESPONSE_PAGE_SIZE = 100;

            DiscussionThreadView.prototype.events = {
                'click .discussion-submit-post': 'submitComment',
                'click .add-response-btn': 'scrollToAddResponse',
                'click .forum-thread-expand': 'expand',
                'click .forum-thread-collapse': 'collapse'
            };

            DiscussionThreadView.prototype.$ = function(selector) {
                return this.$el.find(selector);
            };

            DiscussionThreadView.prototype.isQuestion = function() {
                return this.model.get('thread_type') === 'question';
            };

            DiscussionThreadView.prototype.initialize = function(options) {
                var _ref,
                    self = this;
                DiscussionThreadView.__super__.initialize.call(this);
                this.mode = options.mode || 'inline';
                this.context = options.context || 'course';
                this.options = _.extend({}, options);
                if ((_ref = this.mode) !== 'tab' && _ref !== 'inline') {
                    throw new Error('invalid mode: ' + this.mode);
                }
                this.readOnly = $('.discussion-module').data('read-only');
                this.model.collection.on('reset', function(collection) {
                    var id;
                    id = self.model.get('id');
                    if (collection.get(id)) {
                        self.model = collection.get(id);
                    }
                });
                this.createShowView();
                this.responses = new Comments();
                this.loadedResponses = false;
                if (this.isQuestion()) {
                    this.markedAnswers = new Comments();
                }
            };

            DiscussionThreadView.prototype.rerender = function() {
                if (this.showView) {
                    this.showView.undelegateEvents();
                }
                this.undelegateEvents();
                this.$el.empty();
                this.initialize({
                    mode: this.mode,
                    model: this.model,
                    el: this.el,
                    course_settings: this.options.course_settings,
                    topicId: this.topicId
                });
                return this.render();
            };

            DiscussionThreadView.prototype.renderTemplate = function() {
                var container, templateData;
                this.template = _.template($('#thread-template').html());
                container = $('#discussion-container');
                if (!container.length) {
                    container = $('.discussion-module');
                }
                templateData = _.extend(this.model.toJSON(), {
                    readOnly: this.readOnly,
                    can_create_comment: container.data('user-create-comment')
                });
                return this.template(templateData);
            };

            DiscussionThreadView.prototype.render = function() {
                var self = this;
                var $element = $(this.renderTemplate());
                this.$el.empty();
                this.$el.append($element);
                this.delegateEvents();
                this.renderShowView();
                this.renderAttrs();
                this.$('span.timeago').timeago();
                this.makeWmdEditor('reply-body');
                this.renderAddResponseButton();
                this.responses.on('add', function(response) {
                    return self.renderResponseToList(response, '.js-response-list', {});
                });
                if (this.isQuestion()) {
                    this.markedAnswers.on('add', function(response) {
                        return self.renderResponseToList(response, '.js-marked-answer-list', {
                            collapseComments: true
                        });
                    });
                }
                if (this.mode === 'tab') {
                    setTimeout(function() {
                        return self.loadInitialResponses();
                    }, 100);
                    return this.$('.post-tools').hide();
                } else {
                    return this.collapse();
                }
            };

            DiscussionThreadView.prototype.attrRenderer = $.extend({}, DiscussionContentView.prototype.attrRenderer, {
                closed: function(closed) {
                    this.$('.discussion-reply-new').toggle(!closed);
                    this.$('.comment-form').closest('li').toggle(!closed);
                    this.$('.action-vote').toggle(!closed);
                    this.$('.display-vote').toggle(closed);
                    return this.renderAddResponseButton();
                }
            });

            DiscussionThreadView.prototype.expand = function(event) {
                if (event) {
                    event.preventDefault();
                }
                this.$el.addClass('expanded');
                this.$el.find('.post-body').text(this.model.get('body'));
                this.showView.convertMath();
                this.$el.find('.forum-thread-expand').hide();
                this.$el.find('.forum-thread-collapse').show();
                this.$el.find('.post-extended-content').show();
                if (!this.loadedResponses) {
                    return this.loadInitialResponses();
                }
            };

            DiscussionThreadView.prototype.collapse = function(event) {
                if (event) {
                    event.preventDefault();
                }
                this.$el.removeClass('expanded');
                this.$el.find('.post-body').text(this.getAbbreviatedBody());
                this.showView.convertMath();
                this.$el.find('.forum-thread-expand').show();
                this.$el.find('.forum-thread-collapse').hide();
                return this.$el.find('.post-extended-content').hide();
            };

            DiscussionThreadView.prototype.getAbbreviatedBody = function() {
                var abbreviated, cached;
                cached = this.model.get('abbreviatedBody');
                if (cached) {
                    return cached;
                } else {
                    abbreviated = DiscussionUtil.abbreviateString(this.model.get('body'), 140);
                    this.model.set('abbreviatedBody', abbreviated);
                    return abbreviated;
                }
            };

            DiscussionThreadView.prototype.cleanup = function() {
                // jQuery.ajax after 1.5 returns a jqXHR which doesn't implement .abort
                // but I don't feel confident enough about what's going on here to remove this code
                // so just check to make sure we can abort before we try to
                if (this.responsesRequest && this.responsesRequest.abort) {
                    return this.responsesRequest.abort();
                }
            };

            DiscussionThreadView.prototype.loadResponses = function(responseLimit, $elem, firstLoad) {
                var takeFocus,
                    self = this;
                takeFocus = this.mode === 'tab' ? false : true;
                this.responsesRequest = DiscussionUtil.safeAjax({
                    url: DiscussionUtil.urlFor(
                        'retrieve_single_thread', this.model.get('commentable_id'), this.model.id
                    ),
                    data: {
                        resp_skip: this.responses.size(),
                        resp_limit: responseLimit ? responseLimit : void 0
                    },
                    $elem: $elem,
                    $loading: $elem,
                    takeFocus: takeFocus,
                    complete: function() {
                        self.responsesRequest = null;
                    },
                    success: function(data) {
                        Content.loadContentInfos(data.annotated_content_info);
                        if (self.isQuestion()) {
                            self.markedAnswers.add(data.content.endorsed_responses);
                        }
                        self.responses.add(
                            self.isQuestion() ? data.content.non_endorsed_responses : data.content.children
                        );
                        self.renderResponseCountAndPagination(
                            self.isQuestion() ?
                                data.content.non_endorsed_resp_total :
                                data.content.resp_total
                        );
                        self.trigger('thread:responses:rendered');
                        self.loadedResponses = true;
                        return self.$el.find('.discussion-article[data-id="' + self.model.id + '"]').focus();
                    },
                    error: function(xhr, textStatus) {
                        if (textStatus === 'abort') {
                            return;
                        }
                        if (xhr.status === 404) {
                            DiscussionUtil.discussionAlert(
                                gettext('Error'),
                                gettext('The post you selected has been deleted.')
                            );
                        } else if (firstLoad) {
                            DiscussionUtil.discussionAlert(
                                gettext('Error'),
                                gettext('Responses could not be loaded. Refresh the page to try again.')
                            );
                        } else {
                            DiscussionUtil.discussionAlert(
                                gettext('Error'),
                                gettext('Additional responses could not be loaded. Refresh the page to try again.')
                            );
                        }
                    }
                });
            };

            DiscussionThreadView.prototype.loadInitialResponses = function() {
                return this.loadResponses(INITIAL_RESPONSE_PAGE_SIZE, this.$el.find('.js-response-list'), true);
            };

            DiscussionThreadView.prototype.renderResponseCountAndPagination = function(responseTotal) {
                var buttonText, $loadMoreButton, responseCountFormat, responseLimit, responsePagination,
                    responsesRemaining, showingResponsesText, self = this;
                if (this.isQuestion() && this.markedAnswers.length !== 0) {
                    responseCountFormat = ngettext(
                        '{numResponses} other response', '{numResponses} other responses', responseTotal
                    );
                } else {
                    responseCountFormat = ngettext(
                        '{numResponses} response', '{numResponses} responses', responseTotal
                    );
                }
                this.$el.find('.response-count').text(
                    edx.StringUtils.interpolate(responseCountFormat, {numResponses: responseTotal}, true)
                );
                responsePagination = this.$el.find('.response-pagination');
                responsePagination.empty();
                if (responseTotal > 0) {
                    responsesRemaining = responseTotal - this.responses.size();
                    if (responsesRemaining === 0) {
                        showingResponsesText = gettext('Showing all responses');
                    }
                    else {
                        showingResponsesText = edx.StringUtils.interpolate(
                            ngettext(
                                'Showing first response', 'Showing first {numResponses} responses',
                                this.responses.size()
                            ),
                            {numResponses: this.responses.size()},
                            true
                        );
                    }

                    responsePagination.append($('<span>')
                        .addClass('response-display-count').text(showingResponsesText));
                    if (responsesRemaining > 0) {
                        if (responsesRemaining < SUBSEQUENT_RESPONSE_PAGE_SIZE) {
                            responseLimit = null;
                            buttonText = gettext('Load all responses');
                        } else {
                            responseLimit = SUBSEQUENT_RESPONSE_PAGE_SIZE;
                            buttonText = edx.StringUtils.interpolate(gettext('Load next {numResponses} responses'), {
                                numResponses: responseLimit
                            }, true);
                        }
                        $loadMoreButton = $('<button>')
                            .addClass('btn-neutral')
                            .addClass('load-response-button')
                            .text(buttonText);
                        $loadMoreButton.click(function() {
                            return self.loadResponses(responseLimit, $loadMoreButton);
                        });
                        return responsePagination.append($loadMoreButton);
                    }
                }
            };

            DiscussionThreadView.prototype.renderResponseToList = function(response, listSelector, options) {
                var view;
                response.set('thread', this.model);
                view = new ThreadResponseView($.extend({
                    model: response
                }, options));
                view.on('comment:add', this.addComment);
                view.on('comment:endorse', this.endorseThread);
                view.render();
                this.$el.find(listSelector).append(view.el);
                return view.afterInsert();
            };

            DiscussionThreadView.prototype.renderAddResponseButton = function() {
                if (this.model.hasResponses() && this.model.can('can_reply') && !this.model.get('closed')) {
                    return this.$el.find('div.add-response').show();
                } else {
                    return this.$el.find('div.add-response').hide();
                }
            };

            DiscussionThreadView.prototype.scrollToAddResponse = function(event) {
                var form;
                event.preventDefault();
                form = $(event.target).parents('article.discussion-article').find('form.discussion-reply-new');
                $('html, body').scrollTop(form.offset().top);
                return form.find('.wmd-panel textarea').focus();
            };

            DiscussionThreadView.prototype.addComment = function() {
                return this.model.comment();
            };

            DiscussionThreadView.prototype.endorseThread = function() {
                return this.model.set('endorsed', this.$el.find('.action-answer.is-checked').length > 0);
            };

            DiscussionThreadView.prototype.submitComment = function(event) {
                var body, comment, url;
                event.preventDefault();
                url = this.model.urlFor('reply');
                body = this.getWmdContent('reply-body');
                if (!body.trim().length) {
                    return;
                }
                this.setWmdContent('reply-body', '');
                comment = new Comment({
                    body: body,
                    created_at: (new Date()).toISOString(),
                    username: window.user.get('username'),
                    votes: {
                        up_count: 0
                    },
                    abuse_flaggers: [],
                    endorsed: false,
                    user_id: window.user.get('id')
                });
                comment.set('thread', this.model.get('thread'));
                this.renderResponseToList(comment, '.js-response-list');
                this.model.addComment();
                this.renderAddResponseButton();
                return DiscussionUtil.safeAjax({
                    $elem: $(event.target),
                    url: url,
                    type: 'POST',
                    dataType: 'json',
                    data: {
                        body: body
                    },
                    success: function(data) {
                        comment.updateInfo(data.annotated_content_info);
                        return comment.set(data.content);
                    }
                });
            };

            DiscussionThreadView.prototype.edit = function() {
                this.createEditView();
                return this.renderEditView();
            };

            DiscussionThreadView.prototype.createEditView = function() {
                if (this.showView) {
                    this.showView.undelegateEvents();
                    this.showView.$el.empty();
                    this.showView = null;
                }
                this.editView = new DiscussionThreadEditView({
                    container: this.$('.thread-content-wrapper'),
                    model: this.model,
                    mode: this.mode,
                    context: this.context,
                    course_settings: this.options.course_settings
                });
                this.editView.bind('thread:updated thread:cancel_edit', this.closeEditView);
                return this.editView.bind('comment:endorse', this.endorseThread);
            };

            DiscussionThreadView.prototype.renderSubView = function(view) {
                view.setElement(this.$('.thread-content-wrapper'));
                view.render();
                return view.delegateEvents();
            };

            DiscussionThreadView.prototype.renderEditView = function() {
                return this.editView.render();
            };

            DiscussionThreadView.prototype.createShowView = function() {
                this.showView = new DiscussionThreadShowView({
                    model: this.model,
                    mode: this.mode
                });
                this.showView.bind('thread:_delete', this._delete);
                return this.showView.bind('thread:edit', this.edit);
            };

            DiscussionThreadView.prototype.renderShowView = function() {
                return this.renderSubView(this.showView);
            };

            DiscussionThreadView.prototype.closeEditView = function() {
                this.createShowView();
                this.renderShowView();
                this.renderAttrs();
                return this.$el.find('.post-extended-content').show();
            };

            DiscussionThreadView.prototype._delete = function(event) {
                var $elem, url;
                url = this.model.urlFor('_delete');
                if (!this.model.can('can_delete')) {
                    return;
                }
                if (!confirm(gettext('Are you sure you want to delete this post?'))) {
                    return;
                }
                this.model.remove();
                this.showView.undelegateEvents();
                this.undelegateEvents();
                this.$el.empty();
                $elem = $(event.target);
                return DiscussionUtil.safeAjax({
                    $elem: $elem,
                    url: url,
                    type: 'POST'
                });
            };

            return DiscussionThreadView;
        })(DiscussionContentView);
    }
}).call(window);
