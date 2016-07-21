/* globals Content, Discussion, DiscussionUtil */
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
                this.filterTopics = function() {
                    return DiscussionThreadListView.prototype.filterTopics.apply(self, arguments);
                };
                this.toggleBrowseMenu = function() {
                    return DiscussionThreadListView.prototype.toggleBrowseMenu.apply(self, arguments);
                };
                this.hideBrowseMenu = function() {
                    return DiscussionThreadListView.prototype.hideBrowseMenu.apply(self, arguments);
                };
                this.showBrowseMenu = function() {
                    return DiscussionThreadListView.prototype.showBrowseMenu.apply(self, arguments);
                };
                this.isBrowseMenuVisible = function() {
                    return DiscussionThreadListView.prototype.isBrowseMenuVisible.apply(self, arguments);
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
                this.updateSidebar = function() {
                    return DiscussionThreadListView.prototype.updateSidebar.apply(self, arguments);
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
                return DiscussionThreadListView.__super__.constructor.apply(this, arguments);
            }

            DiscussionThreadListView.prototype.events = {
                "click .forum-nav-browse": "toggleBrowseMenu",
                "keypress .forum-nav-browse-filter-input": function(event) {
                    return DiscussionUtil.ignoreEnterKey(event);
                },
                "keyup .forum-nav-browse-filter-input": "filterTopics",
                "click .forum-nav-browse-menu-wrapper": "ignoreClick",
                "click .forum-nav-browse-title": "selectTopicHandler",
                "keydown .forum-nav-search-input": "performSearch",
                "click .fa-search": "performSearch",
                "change .forum-nav-sort-control": "sortThreads",
                "click .forum-nav-thread-link": "threadSelected",
                "click .forum-nav-load-more-link": "loadMorePages",
                "change .forum-nav-filter-main-control": "chooseFilter",
                "change .forum-nav-filter-cohort-control": "chooseCohort"
            };

            DiscussionThreadListView.prototype.initialize = function(options) {
                var self = this;
                this.courseSettings = options.courseSettings;
                this.displayedCollection = new Discussion(this.collection.models, {
                    pages: this.collection.pages
                });
                this.collection.on("change", this.reloadDisplayedCollection);
                this.discussionIds = "";
                this.collection.on("reset", function(discussion) {
                    var board;
                    board = $(".current-board").html();
                    self.displayedCollection.current_page = discussion.current_page;
                    self.displayedCollection.pages = discussion.pages;
                    return self.displayedCollection.reset(discussion.models);
                });
                this.collection.on("add", this.addAndSelectThread);
                this.collection.on("thread:remove", this.threadRemoved);
                this.sidebar_padding = 10;
                this.boardName = null;
                this.template = _.template($("#thread-list-template").html());
                this.current_search = "";
                this.mode = 'all';
                this.searchAlertCollection = new Backbone.Collection([], {
                    model: Backbone.Model
                });
                this.searchAlertCollection.on("add", function(searchAlert) {
                    var content;
                    content = edx.HtmlUtils.template($("#search-alert-template").html())({
                        'messageHtml': searchAlert.attributes.message,
                        'cid': searchAlert.cid,
                        'css_class': searchAlert.attributes.css_class
                    });
                    edx.HtmlUtils.append(self.$(".search-alerts"), content);
                    return self.$("#search-alert-" + searchAlert.cid + " a.dismiss")
                        .bind("click", searchAlert, function(event) {
                            return self.removeSearchAlert(event.data.cid);
                        });
                });
                this.searchAlertCollection.on("remove", function(searchAlert) {
                    return self.$("#search-alert-" + searchAlert.cid).remove();
                });
                return this.searchAlertCollection.on("reset", function() {
                    return self.$(".search-alerts").empty();
                });
            };

            /**
             * Creates search alert model and adds it to collection
             * @param message - alert message
             * @param css_class - Allows setting custom css class for a message. This can be used to style messages
             *                    of different types differently (i.e. other background, completely hide, etc.)
             * @returns {Backbone.Model}
             */
            DiscussionThreadListView.prototype.addSearchAlert = function(message, css_class) {
                var m;
                if (typeof css_class === 'undefined' || css_class === null) {
                    css_class = "";
                }
                m = new Backbone.Model({"message": message, "css_class": css_class});
                this.searchAlertCollection.add(m);
                return m;
            };

            DiscussionThreadListView.prototype.removeSearchAlert = function(searchAlert) {
                return this.searchAlertCollection.remove(searchAlert);
            };

            DiscussionThreadListView.prototype.clearSearchAlerts = function() {
                return this.searchAlertCollection.reset();
            };

            DiscussionThreadListView.prototype.reloadDisplayedCollection = function(thread) {
                var active, $content, current_el, thread_id;
                this.clearSearchAlerts();
                thread_id = thread.get('id');
                $content = this.renderThread(thread);
                current_el = this.$(".forum-nav-thread[data-id=" + thread_id + "]");
                active = current_el.has(".forum-nav-thread-link.is-active").length !== 0;
                current_el.replaceWith($content);
                this.showMetadataAccordingToSort();
                if (active) {
                    return this.setActiveThread(thread_id);
                }
            };

            /*
             TODO fix this entire chain of events
             */


            DiscussionThreadListView.prototype.addAndSelectThread = function(thread) {
                var commentable_id, menuItem,
                    self = this;
                commentable_id = thread.get("commentable_id");
                menuItem = this.$(".forum-nav-browse-menu-item[data-discussion-id]").filter(function() {
                    return $(this).data("discussion-id") === commentable_id;
                });
                this.setCurrentTopicDisplay(this.getPathText(menuItem));
                return this.retrieveDiscussion(commentable_id, function() {
                    return self.trigger("thread:created", thread.get('id'));
                });
            };

            DiscussionThreadListView.prototype.updateSidebar = function() {
                var amount, browseFilterHeight, discussionBody, discussionBottomOffset, discussionsBodyBottom,
                    discussionsBodyTop, headerHeight, refineBarHeight, scrollTop, sidebar, sidebarHeight, topOffset,
                    windowHeight;
                scrollTop = $(window).scrollTop();
                windowHeight = $(window).height();
                discussionBody = $(".discussion-column");
                discussionsBodyTop = discussionBody[0] ? discussionBody.offset().top : void 0;
                discussionsBodyBottom = discussionsBodyTop + discussionBody.outerHeight();
                sidebar = $(".forum-nav");
                if (scrollTop > discussionsBodyTop - this.sidebar_padding) {
                    sidebar.css('top', scrollTop - discussionsBodyTop + this.sidebar_padding);
                } else {
                    sidebar.css('top', '0');
                }
                sidebarHeight = windowHeight - Math.max(discussionsBodyTop - scrollTop, this.sidebar_padding);
                topOffset = scrollTop + windowHeight;
                discussionBottomOffset = discussionsBodyBottom + this.sidebar_padding;
                amount = Math.max(topOffset - discussionBottomOffset, 0);
                sidebarHeight = sidebarHeight - this.sidebar_padding - amount;
                sidebarHeight = Math.min(sidebarHeight + 1, discussionBody.outerHeight());
                sidebar.css('height', sidebarHeight);
                headerHeight = this.$(".forum-nav-header").outerHeight();
                refineBarHeight = this.$(".forum-nav-refine-bar").outerHeight();
                browseFilterHeight = this.$(".forum-nav-browse-filter").outerHeight();
                this.$('.forum-nav-thread-list')
                    .css('height', (sidebarHeight - headerHeight - refineBarHeight - 2) + 'px');
                this.$('.forum-nav-browse-menu')
                    .css('height', (sidebarHeight - headerHeight - browseFilterHeight - 2) + 'px');
            };

            DiscussionThreadListView.prototype.ignoreClick = function(event) {
                return event.stopPropagation();
            };

            DiscussionThreadListView.prototype.render = function() {
                var self = this,
                    $elem = this.template({
                        isCohorted: this.courseSettings.get("is_cohorted"),
                        isPrivilegedUser: DiscussionUtil.isPrivilegedUser()
                    });
                this.timer = 0;
                this.$el.empty();
                this.$el.append($elem);
                this.$(".forum-nav-sort-control option").removeProp("selected");
                this.$(".forum-nav-sort-control option[value=" + this.collection.sort_preference + "]")
                    .prop("selected", true);
                $(window).bind("load scroll resize", this.updateSidebar);
                this.displayedCollection.on("reset", this.renderThreads);
                this.displayedCollection.on("thread:remove", this.renderThreads);
                this.displayedCollection.on("change:commentable_id", function() {
                    if (self.mode === "commentables") {
                        return self.retrieveDiscussions(self.discussionIds.split(","));
                    }
                });
                this.renderThreads();
                return this;
            };

            DiscussionThreadListView.prototype.renderThreads = function() {
                var $content, thread, i, len;
                this.$(".forum-nav-thread-list").empty();
                for (i = 0, len = this.displayedCollection.models.length; i < len; i++) {
                    thread = this.displayedCollection.models[i];
                    $content = this.renderThread(thread);
                    this.$(".forum-nav-thread-list").append($content);
                }
                this.showMetadataAccordingToSort();
                this.renderMorePages();
                this.updateSidebar();
                this.trigger("threads:rendered");
            };

            DiscussionThreadListView.prototype.showMetadataAccordingToSort = function() {
                var commentCounts, voteCounts;
                voteCounts = this.$(".forum-nav-thread-votes-count");
                commentCounts = this.$(".forum-nav-thread-comments-count");
                voteCounts.hide();
                commentCounts.hide();
                switch (this.$(".forum-nav-sort-control").val()) {
                    case "activity":
                    case "comments":
                        return commentCounts.show();
                    case "votes":
                        return voteCounts.show();
                }
            };

            DiscussionThreadListView.prototype.renderMorePages = function() {
                if (this.displayedCollection.hasMorePages()) {
                    edx.HtmlUtils.append(
                        this.$(".forum-nav-thread-list"),
                        edx.HtmlUtils.template($("#nav-load-more-link").html())({})
                    );
                }
            };

            DiscussionThreadListView.prototype.getLoadingContent = function(srText) {
                return edx.HtmlUtils.template($("#nav-loading-template").html())({srText: srText});
            };

            DiscussionThreadListView.prototype.loadMorePages = function(event) {
                var error, lastThread, loadMoreElem, loadingElem, options, _ref,
                    self = this;
                if (event) {
                    event.preventDefault();
                }
                loadMoreElem = this.$(".forum-nav-load-more");
                loadMoreElem.empty();
                edx.HtmlUtils.append(loadMoreElem, this.getLoadingContent(gettext("Loading more threads")));
                loadingElem = loadMoreElem.find(".forum-nav-loading");
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
                }
                _ref = this.collection.last();
                lastThread = _ref ? _ref.get('id') : void 0;
                if (lastThread) {
                    this.once("threads:rendered", function() {
                        var classSelector =
                            ".forum-nav-thread[data-id='" + lastThread + "'] + .forum-nav-thread " +
                            ".forum-nav-thread-link";
                        return $(classSelector).focus();
                    });
                } else {
                    this.once("threads:rendered", function() {
                        var _ref1 = $(".forum-nav-thread-link").first();
                        return _ref1 ? _ref1.focus() : void 0;
                    });
                }
                error = function() {
                    self.renderThreads();
                    DiscussionUtil.discussionAlert(
                        gettext("Sorry"), gettext("We had some trouble loading more threads. Please try again.")
                    );
                };
                return this.collection.retrieveAnotherPage(this.mode, options, {
                    sort_key: this.$(".forum-nav-sort-control").val()
                }, error);
            };

            DiscussionThreadListView.prototype.renderThread = function(thread) {
                var content, unreadCount;
                content = $(_.template($("#thread-list-item-template").html())(thread.toJSON()));
                unreadCount = thread.get('unread_comments_count') + (thread.get("read") ? 0 : 1);
                if (unreadCount > 0) {
                    content.find('.forum-nav-thread-comments-count').attr(
                        "data-tooltip",
                        edx.StringUtils.interpolate(
                            ngettext('{unread_count} new comment', '{unread_count} new comments', unreadCount),
                            {unread_count: unreadCount},
                            true
                        )
                    );
                }
                return content;
            };

            DiscussionThreadListView.prototype.threadSelected = function(e) {
                var thread_id;
                thread_id = $(e.target).closest(".forum-nav-thread").attr("data-id");
                this.setActiveThread(thread_id);
                this.trigger("thread:selected", thread_id);
                return false;
            };

            DiscussionThreadListView.prototype.threadRemoved = function(thread) {
                this.trigger("thread:removed", thread);
            };

            DiscussionThreadListView.prototype.setActiveThread = function(thread_id) {
                var $srElem;
                this.$(".forum-nav-thread-link").find(".sr").remove();
                this.$(".forum-nav-thread[data-id!='" + thread_id + "'] .forum-nav-thread-link")
                    .removeClass("is-active");
                $srElem = edx.HtmlUtils.joinHtml(
                    edx.HtmlUtils.HTML('<span class="sr">'),
                    edx.HtmlUtils.ensureHtml(gettext("Current conversation")),
                    edx.HtmlUtils.HTML('</span>')
                ).toString();
                this.$(".forum-nav-thread[data-id='" + thread_id + "'] .forum-nav-thread-link")
                    .addClass("is-active").find(".forum-nav-thread-wrapper-1")
                    .prepend($srElem);
            };

            DiscussionThreadListView.prototype.goHome = function() {
                var url, $tpl_content;
                this.template = _.template($("#discussion-home-template").html());
                $tpl_content = $(this.template());
                $(".forum-content").empty().append($tpl_content);
                $(".forum-nav-thread-list a").removeClass("is-active").find(".sr").remove();
                $("input.email-setting").bind("click", this.updateEmailNotifications);
                url = DiscussionUtil.urlFor("notifications_status", window.user.get("id"));
                DiscussionUtil.safeAjax({
                    url: url,
                    type: "GET",
                    success: function(response) {
                        $('input.email-setting').prop('checked', response.status);
                    }
                });
            };

            DiscussionThreadListView.prototype.isBrowseMenuVisible = function() {
                return this.$(".forum-nav-browse-menu-wrapper").is(":visible");
            };

            DiscussionThreadListView.prototype.showBrowseMenu = function() {
                if (!this.isBrowseMenuVisible()) {
                    this.$(".forum-nav-browse").addClass("is-active");
                    this.$(".forum-nav-browse-menu-wrapper").show();
                    this.$(".forum-nav-thread-list-wrapper").hide();
                    $(".forum-nav-browse-filter-input").focus();
                    $("body").bind("click", this.hideBrowseMenu);
                    return this.updateSidebar();
                }
            };

            DiscussionThreadListView.prototype.hideBrowseMenu = function() {
                if (this.isBrowseMenuVisible()) {
                    this.$(".forum-nav-browse").removeClass("is-active");
                    this.$(".forum-nav-browse-menu-wrapper").hide();
                    this.$(".forum-nav-thread-list-wrapper").show();
                    $("body").unbind("click", this.hideBrowseMenu);
                    return this.updateSidebar();
                }
            };

            DiscussionThreadListView.prototype.toggleBrowseMenu = function(event) {
                event.preventDefault();
                event.stopPropagation();
                if (this.isBrowseMenuVisible()) {
                    return this.hideBrowseMenu();
                } else {
                    return this.showBrowseMenu();
                }
            };

            DiscussionThreadListView.prototype.getPathText = function(item) {
                var path, pathTitles;
                path = item.parents(".forum-nav-browse-menu-item").andSelf();
                pathTitles = path.children(".forum-nav-browse-title").map(function(i, elem) {
                    return $(elem).text();
                }).get();
                return pathTitles.join(" / ");
            };

            DiscussionThreadListView.prototype.filterTopics = function(event) {
                var items, query,
                    self = this;
                query = $(event.target).val();
                items = this.$(".forum-nav-browse-menu-item");
                if (query.length === 0) {
                    return items.show();
                } else {
                    items.hide();
                    return items.each(function(i, item) {
                        var path, pathText;
                        item = $(item);
                        if (!item.is(":visible")) {
                            pathText = self.getPathText(item).toLowerCase();
                            if (query.split(" ").every(function(term) {
                                    return pathText.search(term.toLowerCase()) !== -1;
                                })) {
                                path = item.parents(".forum-nav-browse-menu-item").andSelf();
                                return path.add(item.find(".forum-nav-browse-menu-item")).show();
                            }
                        }
                    });
                }
            };

            DiscussionThreadListView.prototype.setCurrentTopicDisplay = function(text) {
                return this.$(".forum-nav-browse-current").text(this.fitName(text));
            };

            DiscussionThreadListView.prototype.getNameWidth = function(name) {
                var $test, width;
                $test = $("<div>");
                $test.css({
                    "font-size": this.$(".forum-nav-browse-current").css('font-size'),
                    opacity: 0,
                    position: 'absolute',
                    left: -1000,
                    top: -1000
                });
                $("body").append($test);
                $test.text(name);
                width = $test.width();
                $test.remove();
                return width;
            };

            DiscussionThreadListView.prototype.fitName = function(name) {
                var partialName, path, prefix, rawName, width, x;
                this.maxNameWidth = this.$(".forum-nav-browse").width() -
                    this.$(".forum-nav-browse .icon").outerWidth(true) -
                    this.$(".forum-nav-browse-drop-arrow").outerWidth(true);
                width = this.getNameWidth(name);
                if (width < this.maxNameWidth) {
                    return name;
                }
                path = (function() {
                    var _i, _len, _ref, _results;
                    _ref = name.split("/");
                    _results = [];
                    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                        x = _ref[_i];
                        _results.push(x.replace(/^\s+|\s+$/g, ""));
                    }
                    return _results;
                })();
                prefix = "";
                while (path.length > 1) {
                    prefix = gettext("…") + "/";
                    path.shift();
                    partialName = prefix + path.join("/");
                    if (this.getNameWidth(partialName) < this.maxNameWidth) {
                        return partialName;
                    }
                }
                rawName = path[0];
                name = prefix + rawName;
                while (this.getNameWidth(name) > this.maxNameWidth) {
                    rawName = rawName.slice(0, rawName.length - 1);
                    name = prefix + rawName + gettext("…");
                }
                return name;
            };

            DiscussionThreadListView.prototype.selectTopicHandler = function(event) {
                event.preventDefault();
                return this.selectTopic($(event.target));
            };

            DiscussionThreadListView.prototype.selectTopic = function($target) {
                var allItems, discussionIds, item;
                this.hideBrowseMenu();
                this.clearSearch();
                item = $target.closest('.forum-nav-browse-menu-item');
                this.setCurrentTopicDisplay(this.getPathText(item));
                if (item.hasClass("forum-nav-browse-menu-all")) {
                    this.discussionIds = "";
                    this.$('.forum-nav-filter-cohort').show();
                    return this.retrieveAllThreads();
                } else if (item.hasClass("forum-nav-browse-menu-following")) {
                    this.retrieveFollowed();
                    return this.$('.forum-nav-filter-cohort').hide();
                } else {
                    allItems = item.find(".forum-nav-browse-menu-item").andSelf();
                    discussionIds = allItems.filter("[data-discussion-id]").map(function(i, elem) {
                        return $(elem).data("discussion-id");
                    }).get();
                    this.retrieveDiscussions(discussionIds);
                    return this.$(".forum-nav-filter-cohort").toggle(item.data('cohorted') === true);
                }
            };

            DiscussionThreadListView.prototype.chooseFilter = function() {
                this.filter = $(".forum-nav-filter-main-control :selected").val();
                return this.retrieveFirstPage();
            };

            DiscussionThreadListView.prototype.chooseCohort = function() {
                this.group_id = this.$('.forum-nav-filter-cohort-control :selected').val();
                return this.retrieveFirstPage();
            };

            DiscussionThreadListView.prototype.retrieveDiscussion = function(discussion_id, callback) {
                var url, self = this;
                url = DiscussionUtil.urlFor("retrieve_discussion", discussion_id);
                return DiscussionUtil.safeAjax({
                    url: url,
                    type: "GET",
                    success: function(response) {
                        self.collection.current_page = response.page;
                        self.collection.pages = response.num_pages;
                        self.collection.reset(response.discussion_data);
                        Content.loadContentInfos(response.annotated_content_info);
                        self.displayedCollection.reset(self.collection.models);
                        if (callback) {
                            return callback();
                        }
                    }
                });
            };

            DiscussionThreadListView.prototype.retrieveDiscussions = function(discussion_ids) {
                this.discussionIds = discussion_ids.join(',');
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
                this.displayedCollection.setSortComparator(this.$(".forum-nav-sort-control").val());
                return this.retrieveFirstPage(event);
            };

            DiscussionThreadListView.prototype.performSearch = function(event) {
                /*
                 event.which 13 represent the Enter button
                 */

                var text;
                if (event.which === 13 || event.type === 'click') {
                    event.preventDefault();
                    this.hideBrowseMenu();
                    this.setCurrentTopicDisplay(gettext("Search Results"));
                    text = this.$(".forum-nav-search-input").val();
                    return this.searchFor(text);
                }
            };

            DiscussionThreadListView.prototype.searchFor = function(text) {
                var url, self = this;
                this.clearSearchAlerts();
                this.clearFilters();
                this.mode = 'search';
                this.current_search = text;
                url = DiscussionUtil.urlFor("search");
                /*
                 TODO: This might be better done by setting discussion.current_page=0 and
                 calling discussion.loadMorePages
                 Mainly because this currently does not reset any pagination variables which could cause problems.
                 This doesn't use pagination either.
                */

                return DiscussionUtil.safeAjax({
                    $elem: this.$(".forum-nav-search-input"),
                    data: {
                        text: text
                    },
                    url: url,
                    type: "GET",
                    dataType: 'json',
                    $loading: $,
                    loadingCallback: function() {
                        var element = self.$(".forum-nav-thread-list");
                        element.empty();
                        edx.HtmlUtils.append(
                            element,
                            edx.HtmlUtils.joinHtml(
                                edx.HtmlUtils.HTML("<li class='forum-nav-load-more'>"),
                                    self.getLoadingContent(gettext("Loading thread list")),
                                edx.HtmlUtils.HTML("</li>")
                            )
                        );
                    },
                    loadedCallback: function() {
                        return self.$(".forum-nav-thread-list .forum-nav-load-more").remove();
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
                                        "original_query": edx.HtmlUtils.joinHtml(
                                            edx.HtmlUtils.HTML("<em>"), text, edx.HtmlUtils.HTML("</em>")
                                        ),
                                        "suggested_query": edx.HtmlUtils.joinHtml(
                                            edx.HtmlUtils.HTML("<em>"),
                                            response.corrected_text ,
                                            edx.HtmlUtils.HTML("</em>")
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
                    }
                });
            };

            DiscussionThreadListView.prototype.searchForUser = function(text) {
                var self = this;
                return DiscussionUtil.safeAjax({
                    data: {
                        username: text
                    },
                    url: DiscussionUtil.urlFor("users"),
                    type: "GET",
                    dataType: 'json',
                    error: function() {},
                    success: function(response) {
                        var message, username;
                        if (response.users.length > 0) {
                            username = edx.HtmlUtils.joinHtml(
                                edx.HtmlUtils.interpolateHtml(
                                    edx.HtmlUtils.HTML('<a class="link-jump" href="{url}">'),
                                    {url: DiscussionUtil.urlFor("user_profile", response.users[0].id)}
                                ),
                                response.users[0].username,
                                edx.HtmlUtils.HTML("</a>")
                            );

                            message = edx.HtmlUtils.interpolateHtml(
                                gettext('Show posts by {username}.'), {"username": username}
                            );
                            return self.addSearchAlert(message, 'search-by-user');
                        }
                    }
                });
            };

            DiscussionThreadListView.prototype.clearSearch = function() {
                this.$(".forum-nav-search-input").val("");
                this.current_search = "";
                return this.clearSearchAlerts();
            };

            DiscussionThreadListView.prototype.clearFilters = function() {
                this.$(".forum-nav-filter-main-control").val("all");
                return this.$(".forum-nav-filter-cohort-control").val("all");
            };

            DiscussionThreadListView.prototype.retrieveFollowed = function() {
                this.mode = 'followed';
                return this.retrieveFirstPage();
            };

            DiscussionThreadListView.prototype.updateEmailNotifications = function() {
                var $checkbox, checked, urlName;
                $checkbox = $('input.email-setting');
                checked = $checkbox.prop('checked');
                urlName = (checked) ? "enable_notifications" : "disable_notifications";
                DiscussionUtil.safeAjax({
                    url: DiscussionUtil.urlFor(urlName),
                    type: "POST",
                    error: function() {
                        $checkbox.prop('checked', !checked);
                    }
                });
            };

            return DiscussionThreadListView;

        }).call(this, Backbone.View);
    }

}).call(window);
