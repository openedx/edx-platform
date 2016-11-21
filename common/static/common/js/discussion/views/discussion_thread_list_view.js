/* globals _, Backbone, Content, Discussion, DiscussionUtil, DiscussionThreadView, DiscussionThreadListView */
(function() {
    'use strict';
    /* eslint-disable */
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
        /* eslint-enable */

    if (typeof Backbone !== 'undefined' && Backbone !== null) {
        this.DiscussionThreadListView = (function(_super) {
            __extends(DiscussionThreadListView, _super);

            function DiscussionThreadListView() {
                var self = this;
                this.updateEmailNotifications = function() {
                    return DiscussionThreadListView.prototype.updateEmailNotifications.apply(self, arguments);
                };
                this.retrieveFollowed = function() {
                    return DiscussionThreadListView.prototype.retrieveFollowed.apply(self, arguments);
                };
                this.chooseCohort = function() {
                    return DiscussionThreadListView.prototype.chooseCohort.apply(self, arguments);
                };
                this.chooseFilter = function() {
                    return DiscussionThreadListView.prototype.chooseFilter.apply(self, arguments);
                };
                this.threadRemoved = function() {
                    return DiscussionThreadListView.prototype.threadRemoved.apply(self, arguments);
                };
                this.threadSelected = function() {
                    return DiscussionThreadListView.prototype.threadSelected.apply(self, arguments);
                };
                this.renderThread = function() {
                    return DiscussionThreadListView.prototype.renderThread.apply(self, arguments);
                };
                this.loadMorePages = function() {
                    return DiscussionThreadListView.prototype.loadMorePages.apply(self, arguments);
                };
                this.showMetadataAccordingToSort = function() {
                    return DiscussionThreadListView.prototype.showMetadataAccordingToSort.apply(self, arguments);
                };
                this.renderThreads = function() {
                    return DiscussionThreadListView.prototype.renderThreads.apply(self, arguments);
                };
                this.addAndSelectThread = function() {
                    return DiscussionThreadListView.prototype.addAndSelectThread.apply(self, arguments);
                };
                this.reloadDisplayedCollection = function() {
                    return DiscussionThreadListView.prototype.reloadDisplayedCollection.apply(self, arguments);
                };
                this.clearSearchAlerts = function() {
                    return DiscussionThreadListView.prototype.clearSearchAlerts.apply(self, arguments);
                };
                this.removeSearchAlert = function() {
                    return DiscussionThreadListView.prototype.removeSearchAlert.apply(self, arguments);
                };
                this.addSearchAlert = function() {
                    return DiscussionThreadListView.prototype.addSearchAlert.apply(self, arguments);
                };
                this.performSearch = function() {
                    return DiscussionThreadListView.prototype.performSearch.apply(self, arguments);
                };
                return DiscussionThreadListView.__super__.constructor.apply(this, arguments); // eslint-disable-line no-underscore-dangle, max-len
            }

            DiscussionThreadListView.prototype.events = {
                'keypress .forum-nav-browse-filter-input': function(event) {
                    return DiscussionUtil.ignoreEnterKey(event);
                },
                'change .forum-nav-sort-control': 'sortThreads',
                'click .forum-nav-thread-link': 'threadSelected',
                'click .forum-nav-load-more-link': 'loadMorePages',
                'change .forum-nav-filter-main-control': 'chooseFilter',
                'change .forum-nav-filter-cohort-control': 'chooseCohort'
            };

            DiscussionThreadListView.prototype.initialize = function(options) {
                var self = this;
                this.courseSettings = options.courseSettings;
                this.displayedCollection = new Discussion(this.collection.models, {
                    pages: this.collection.pages
                });
                this.collection.on('change', this.reloadDisplayedCollection);
                this.discussionIds = '';
                this.collection.on('reset', function(discussion) {
                    self.displayedCollection.current_page = discussion.current_page;
                    self.displayedCollection.pages = discussion.pages;
                    return self.displayedCollection.reset(discussion.models);
                });
                this.collection.on('add', this.addAndSelectThread);
                this.collection.on('thread:remove', this.threadRemoved);
                this.sidebar_padding = 10;
                this.boardName = null;
                this.current_search = '';
                this.mode = 'all';
                this.showThreadPreview = true;
                this.searchAlertCollection = new Backbone.Collection([], {
                    model: Backbone.Model
                });
                this.searchAlertCollection.on('add', function(searchAlert) {
                    var content;
                    content = edx.HtmlUtils.template($('#search-alert-template').html())({
                        messageHtml: searchAlert.attributes.message,
                        cid: searchAlert.cid,
                        css_class: searchAlert.attributes.css_class
                    });
                    edx.HtmlUtils.append(self.$('.search-alerts'), content);
                    return self.$('#search-alert-' + searchAlert.cid + ' .dismiss')
                        .bind('click', searchAlert, function(event) {
                            return self.removeSearchAlert(event.data.cid);
                        });
                });
                this.searchAlertCollection.on('remove', function(searchAlert) {
                    return self.$('#search-alert-' + searchAlert.cid).remove();
                });
                this.searchAlertCollection.on('reset', function() {
                    return self.$('.search-alerts').empty();
                });
                this.template = edx.HtmlUtils.template($('#thread-list-template').html());
                this.threadListItemTemplate = edx.HtmlUtils.template($('#thread-list-item-template').html());
            };

            /**
             * Creates search alert model and adds it to collection
             * @param message - alert message
             * @param cssClass - Allows setting custom css class for a message. This can be used to style messages
             *                   of different types differently (i.e. other background, completely hide, etc.)
             * @returns {Backbone.Model}
             */
            DiscussionThreadListView.prototype.addSearchAlert = function(message, cssClass) {
                var searchAlertModel = new Backbone.Model({message: message, css_class: cssClass || ''});
                this.searchAlertCollection.add(searchAlertModel);
                return searchAlertModel;
            };

            DiscussionThreadListView.prototype.removeSearchAlert = function(searchAlert) {
                return this.searchAlertCollection.remove(searchAlert);
            };

            DiscussionThreadListView.prototype.clearSearchAlerts = function() {
                return this.searchAlertCollection.reset();
            };

            DiscussionThreadListView.prototype.reloadDisplayedCollection = function(thread) {
                var active, $content, $currentElement, threadId;
                this.clearSearchAlerts();
                threadId = thread.get('id');
                $content = this.renderThread(thread);
                $currentElement = this.$('.forum-nav-thread[data-id=' + threadId + ']');
                active = $currentElement.has('.forum-nav-thread-link.is-active').length !== 0;
                $currentElement.replaceWith($content);
                this.showMetadataAccordingToSort();
                if (active) {
                    this.setActiveThread(threadId);
                }
            };

            /*
             TODO fix this entire chain of events
             */

            DiscussionThreadListView.prototype.addAndSelectThread = function(thread) {
                var commentableId = thread.get('commentable_id'),
                    self = this;
                return this.retrieveDiscussion(commentableId, function() {
                    return self.trigger('thread:created', thread.get('id'));
                });
            };

            DiscussionThreadListView.prototype.ignoreClick = function(event) {
                return event.stopPropagation();
            };

            DiscussionThreadListView.prototype.render = function() {
                var self = this;
                this.timer = 0;
                this.$el.empty();
                edx.HtmlUtils.append(
                    this.$el,
                    this.template({
                        isCohorted: this.courseSettings.get('is_cohorted'),
                        isPrivilegedUser: DiscussionUtil.isPrivilegedUser()
                    })
                );
                this.$('.forum-nav-sort-control option').removeProp('selected');
                this.$('.forum-nav-sort-control option[value=' + this.collection.sort_preference + ']')
                    .prop('selected', true);
                this.displayedCollection.on('reset', this.renderThreads);
                this.displayedCollection.on('thread:remove', this.renderThreads);
                this.displayedCollection.on('change:commentable_id', function() {
                    if (self.mode === 'commentables') {
                        self.retrieveDiscussions(self.discussionIds.split(','));
                    }
                });
                this.renderThreads();
                return this;
            };

            DiscussionThreadListView.prototype.renderThreads = function() {
                var $content, thread, i, len;
                this.$('.forum-nav-thread-list').empty();
                for (i = 0, len = this.displayedCollection.models.length; i < len; i++) {
                    thread = this.displayedCollection.models[i];
                    $content = this.renderThread(thread);
                    this.$('.forum-nav-thread-list').append($content);
                }
                this.showMetadataAccordingToSort();
                this.renderMorePages();
                this.trigger('threads:rendered');
            };

            DiscussionThreadListView.prototype.showMetadataAccordingToSort = function() {
                var voteCounts = this.$('.forum-nav-thread-votes-count'),
                    unreadCommentCounts = this.$('.forum-nav-thread-unread-comments-count'),
                    commentCounts = this.$('.forum-nav-thread-comments-count');
                voteCounts.hide();
                commentCounts.hide();
                unreadCommentCounts.hide();
                switch (this.$('.forum-nav-sort-control').val()) {
                case 'votes':
                    voteCounts.show();
                    break;
                default:
                    unreadCommentCounts.show();
                    commentCounts.show();
                }
            };

            DiscussionThreadListView.prototype.renderMorePages = function() {
                if (this.displayedCollection.hasMorePages()) {
                    edx.HtmlUtils.append(
                        this.$('.forum-nav-thread-list'),
                        edx.HtmlUtils.template($('#nav-load-more-link').html())({})
                    );
                }
            };

            DiscussionThreadListView.prototype.getLoadingContent = function(srText) {
                return edx.HtmlUtils.template($('#nav-loading-template').html())({srText: srText});
            };

            DiscussionThreadListView.prototype.loadMorePages = function(event) {
                var error, lastThread, loadMoreElem, loadingElem, options, ref,
                    self = this;
                if (event) {
                    event.preventDefault();
                }
                loadMoreElem = this.$('.forum-nav-load-more');
                loadMoreElem.empty();
                edx.HtmlUtils.append(loadMoreElem, this.getLoadingContent(gettext('Loading more threads')));
                loadingElem = loadMoreElem.find('.forum-nav-loading');
                DiscussionUtil.makeFocusTrap(loadingElem);
                loadingElem.focus();
                options = {
                    filter: this.filter
                };
                switch (this.mode) {
                case 'search':
                    options.search_text = this.current_search;
                    if (this.group_id) {
                        options.group_id = this.group_id;
                    }
                    break;
                case 'followed':
                    options.user_id = window.user.id;
                    break;
                case 'commentables':
                    options.commentable_ids = this.discussionIds;
                    if (this.group_id) {
                        options.group_id = this.group_id;
                    }
                    break;
                case 'all':
                    if (this.group_id) {
                        options.group_id = this.group_id;
                    }
                    break;
                default:
                }
                ref = this.collection.last();
                lastThread = ref ? ref.get('id') : void 0;
                if (lastThread) {
                    this.once('threads:rendered', function() {
                        var classSelector =
                            ".forum-nav-thread[data-id='" + lastThread + "'] + .forum-nav-thread " +
                            '.forum-nav-thread-link';
                        return $(classSelector).focus();
                    });
                } else {
                    this.once('threads:rendered', function() {
                        var ref1 = $('.forum-nav-thread-link').first();
                        return ref1 ? ref1.focus() : void 0;
                    });
                }
                error = function() {
                    self.renderThreads();
                    DiscussionUtil.discussionAlert(
                        gettext('Sorry'), gettext('We had some trouble loading more threads. Please try again.')
                    );
                };
                return this.collection.retrieveAnotherPage(this.mode, options, {
                    sort_key: this.$('.forum-nav-sort-control').val()
                }, error);
            };

            DiscussionThreadListView.prototype.containsMarkup = function(threadBody) {
                var imagePostSearchString = '![',
                    mathJaxSearchString = /\$/g,
                    containsImages = threadBody.indexOf(imagePostSearchString) !== -1,
                    // mathJax has to have at least 2 dollar signs
                    containsMathJax = (threadBody.match(mathJaxSearchString) || []).length > 1;
                return containsImages || containsMathJax;
            };

            DiscussionThreadListView.prototype.renderThread = function(thread) {
                var threadCommentCount = thread.get('comments_count'),
                    threadUnreadCommentCount = thread.get('unread_comments_count'),
                    neverRead = !thread.get('read') && threadUnreadCommentCount === threadCommentCount,
                    threadPreview = this.containsMarkup(thread.get('body')) ? '' : thread.get('body'),
                    context = _.extend(
                        {
                            neverRead: neverRead,
                            threadUrl: thread.urlFor('retrieve'),
                            threadPreview: threadPreview,
                            showThreadPreview: this.showThreadPreview
                        },
                        thread.toJSON()
                    );
                return $(this.threadListItemTemplate(context).toString());
            };

            DiscussionThreadListView.prototype.threadSelected = function(e) {
                var threadId;
                threadId = $(e.target).closest('.forum-nav-thread').attr('data-id');
                this.setActiveThread(threadId);
                this.trigger('thread:selected', threadId);
                return false;
            };

            DiscussionThreadListView.prototype.threadRemoved = function(thread) {
                this.trigger('thread:removed', thread);
            };

            DiscussionThreadListView.prototype.setActiveThread = function(threadId) {
                var $srElem;
                this.$('.forum-nav-thread-link').find('.sr').remove();
                this.$(".forum-nav-thread[data-id!='" + threadId + "'] .forum-nav-thread-link")
                    .removeClass('is-active');
                $srElem = edx.HtmlUtils.joinHtml(
                    edx.HtmlUtils.HTML('<span class="sr">'),
                    edx.HtmlUtils.ensureHtml(gettext('Current conversation')),
                    edx.HtmlUtils.HTML('</span>')
                ).toString();
                this.$(".forum-nav-thread[data-id='" + threadId + "'] .forum-nav-thread-link")
                    .addClass('is-active').find('.forum-nav-thread-wrapper-1')
                    .prepend($srElem);
            };

            DiscussionThreadListView.prototype.selectTopic = function($target) {
                var allItems, discussionIds, $item;
                $item = $target.closest('.forum-nav-browse-menu-item');

                if ($item.hasClass('forum-nav-browse-menu-all')) {
                    this.discussionIds = '';
                    this.$('.forum-nav-filter-cohort').show();
                    return this.retrieveAllThreads();
                } else if ($item.hasClass('forum-nav-browse-menu-following')) {
                    this.retrieveFollowed();
                    return this.$('.forum-nav-filter-cohort').hide();
                } else {
                    allItems = $item.find('.forum-nav-browse-menu-item').andSelf();
                    discussionIds = allItems.filter('[data-discussion-id]').map(function(i, elem) {
                        return $(elem).data('discussion-id');
                    }).get();
                    this.retrieveDiscussions(discussionIds);
                    return this.$('.forum-nav-filter-cohort').toggle($item.data('cohorted') === true);
                }
            };

            DiscussionThreadListView.prototype.chooseFilter = function() {
                this.filter = $('.forum-nav-filter-main-control :selected').val();
                return this.retrieveFirstPage();
            };

            DiscussionThreadListView.prototype.chooseCohort = function() {
                this.group_id = this.$('.forum-nav-filter-cohort-control :selected').val();
                return this.retrieveFirstPage();
            };

            DiscussionThreadListView.prototype.retrieveDiscussion = function(discussionId, callback) {
                var url = DiscussionUtil.urlFor('retrieve_discussion', discussionId),
                    self = this;
                return DiscussionUtil.safeAjax({
                    url: url,
                    type: 'GET',
                    success: function(response) {
                        self.collection.current_page = response.page;
                        self.collection.pages = response.num_pages;
                        self.collection.reset(response.discussion_data);
                        Content.loadContentInfos(response.annotated_content_info);
                        self.displayedCollection.reset(self.collection.models);
                        if (callback) {
                            callback();
                        }
                    }
                });
            };

            DiscussionThreadListView.prototype.retrieveDiscussions = function(discussionIds) {
                this.discussionIds = discussionIds.join(',');
                this.mode = 'commentables';
                return this.retrieveFirstPage();
            };

            DiscussionThreadListView.prototype.retrieveAllThreads = function() {
                this.mode = 'all';
                return this.retrieveFirstPage();
            };

            DiscussionThreadListView.prototype.retrieveFirstPage = function(event) {
                this.collection.current_page = 0;
                this.collection.reset();
                return this.loadMorePages(event);
            };

            DiscussionThreadListView.prototype.sortThreads = function(event) {
                this.displayedCollection.setSortComparator(this.$('.forum-nav-sort-control').val());
                return this.retrieveFirstPage(event);
            };

            DiscussionThreadListView.prototype.performSearch = function($searchInput) {
                // trigger this event so the breadcrumbs can update as well
                this.trigger('search:initiated');
                this.searchFor($searchInput.val(), $searchInput);
            };

            DiscussionThreadListView.prototype.searchFor = function(text, $searchInput) {
                var url = DiscussionUtil.urlFor('search'),
                    self = this;
                this.clearSearchAlerts();
                this.clearFilters();
                this.mode = 'search';
                this.current_search = text;
                /*
                 TODO: This might be better done by setting discussion.current_page=0 and
                 calling discussion.loadMorePages
                 Mainly because this currently does not reset any pagination variables which could cause problems.
                 This doesn't use pagination either.
                 */

                return DiscussionUtil.safeAjax({
                    $elem: $searchInput,
                    data: {
                        text: text
                    },
                    url: url,
                    type: 'GET',
                    dataType: 'json',
                    $loading: $,
                    loadingCallback: function() {
                        var element = self.$('.forum-nav-thread-list');
                        element.empty();
                        edx.HtmlUtils.append(
                            element,
                            edx.HtmlUtils.joinHtml(
                                edx.HtmlUtils.HTML("<li class='forum-nav-load-more'>"),
                                    self.getLoadingContent(gettext('Loading thread list')),
                                edx.HtmlUtils.HTML('</li>')
                            )
                        );
                    },
                    loadedCallback: function() {
                        return self.$('.forum-nav-thread-list .forum-nav-load-more').remove();
                    },
                    success: function(response, textStatus) {
                        var message, noResponseMsg;
                        if (textStatus === 'success') {
                            self.collection.reset(response.discussion_data);
                            Content.loadContentInfos(response.annotated_content_info);
                            self.collection.current_page = response.page;
                            self.collection.pages = response.num_pages;
                            if (!_.isNull(response.corrected_text)) {
                                noResponseMsg = _.escape(
                                    gettext(
                                        'No results found for {original_query}. ' +
                                        'Showing results for {suggested_query}.'
                                    )
                                );
                                message = edx.HtmlUtils.interpolateHtml(
                                    noResponseMsg,
                                    {
                                        original_query: edx.HtmlUtils.joinHtml(
                                            edx.HtmlUtils.HTML('<em>'), text, edx.HtmlUtils.HTML('</em>')
                                        ),
                                        suggested_query: edx.HtmlUtils.joinHtml(
                                            edx.HtmlUtils.HTML('<em>'),
                                            response.corrected_text,
                                            edx.HtmlUtils.HTML('</em>')
                                        )
                                    }
                                );
                                self.addSearchAlert(message);
                            } else if (response.discussion_data.length === 0) {
                                self.addSearchAlert(gettext('No threads matched your query.'));
                            }
                            self.displayedCollection.reset(self.collection.models);
                            if (text) {
                                return self.searchForUser(text);
                            }
                        }
                        return response;
                    }
                });
            };

            DiscussionThreadListView.prototype.searchForUser = function(text) {
                var self = this;
                return DiscussionUtil.safeAjax({
                    data: {
                        username: text
                    },
                    url: DiscussionUtil.urlFor('users'),
                    type: 'GET',
                    dataType: 'json',
                    error: function() {},
                    success: function(response) {
                        var message, username;
                        if (response.users.length > 0) {
                            username = edx.HtmlUtils.joinHtml(
                                edx.HtmlUtils.interpolateHtml(
                                    edx.HtmlUtils.HTML('<a class="link-jump" href="{url}">'),
                                    {url: DiscussionUtil.urlFor('user_profile', response.users[0].id)}
                                ),
                                response.users[0].username,
                                edx.HtmlUtils.HTML('</a>')
                            );

                            message = edx.HtmlUtils.interpolateHtml(
                                gettext('Show posts by {username}.'), {username: username}
                            );
                            self.addSearchAlert(message, 'search-by-user');
                        }
                    }
                });
            };

            DiscussionThreadListView.prototype.clearFilters = function() {
                this.$('.forum-nav-filter-main-control').val('all');
                return this.$('.forum-nav-filter-cohort-control').val('all');
            };

            DiscussionThreadListView.prototype.retrieveFollowed = function() {
                this.mode = 'followed';
                return this.retrieveFirstPage();
            };

            DiscussionThreadListView.prototype.updateEmailNotifications = function() {
                var $checkbox, checked, urlName;
                $checkbox = $('input.email-setting');
                checked = $checkbox.prop('checked');
                urlName = (checked) ? 'enable_notifications' : 'disable_notifications';
                DiscussionUtil.safeAjax({
                    url: DiscussionUtil.urlFor(urlName),
                    type: 'POST',
                    error: function() {
                        $checkbox.prop('checked', !checked);
                    }
                });
            };

            return DiscussionThreadListView;
        }).call(this, Backbone.View);
    }
}).call(window);
