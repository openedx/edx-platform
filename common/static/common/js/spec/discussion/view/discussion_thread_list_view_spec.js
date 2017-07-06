/* globals
    Discussion, DiscussionCourseSettings, DiscussionViewSpecHelper, DiscussionSpecHelper,
    DiscussionThreadListView, DiscussionUtil, Thread
*/
(function() {
    'use strict';
    describe("DiscussionThreadListView", function() {
        var checkThreadsOrdering, expectFilter, makeView, renderSingleThreadWithProps, setupAjax;

        beforeEach(function() {
            var deferred;
            DiscussionSpecHelper.setUpGlobals();
            DiscussionSpecHelper.setUnderscoreFixtures();
            // suppressing Line is too long (4272 characters!)
            /* jshint -W101 */
            appendSetFixtures("<script type=\"text/template\" id=\"thread-list-template\">\n    <div class=\"forum-nav-header\">\n        <button type=\"button\" class=\"forum-nav-browse\" id=\"forum-nav-browse\" aria-haspopup=\"true\">\n            <span class=\"icon fa fa-bars\" aria-hidden=\"true\"></span>\n            <span class=\"sr\">Discussion topics; currently listing: </span>\n            <span class=\"forum-nav-browse-current\">All Discussions</span>\n            ▾\n        </button>\n        <form class=\"forum-nav-search\">\n            <label>\n                <span class=\"sr\">Search all posts</span>\n                <input class=\"forum-nav-search-input\" id=\"forum-nav-search\" type=\"text\" placeholder=\"Search all posts\">\n                <span class=\"icon fa fa-search\" aria-hidden=\"true\"></span>\n            </label>\n        </form>\n    </div>\n    <div class=\"forum-nav-browse-menu-wrapper\" style=\"display: none\">\n        <form class=\"forum-nav-browse-filter\">\n            <label>\n                <span class=\"sr\">Filter Topics</span>\n                <input type=\"text\" class=\"forum-nav-browse-filter-input\" placeholder=\"filter topics\">\n            </label>\n        </form>\n        <ul class=\"forum-nav-browse-menu\">\n            <li class=\"forum-nav-browse-menu-item forum-nav-browse-menu-all\">\n                <a href=\"#\" class=\"forum-nav-browse-title\">All Discussions</a>\n            </li>\n            <li class=\"forum-nav-browse-menu-item forum-nav-browse-menu-following\">\n                <a href=\"#\" class=\"forum-nav-browse-title\"><span class=\"icon fa fa-star\" aria-hidden=\"true\"></span>Posts I'm Following</a>\n            </li>\n            <li class=\"forum-nav-browse-menu-item\">\n                <a href=\"#\" class=\"forum-nav-browse-title\">Parent</a>\n                <ul class=\"forum-nav-browse-submenu\">\n                    <li class=\"forum-nav-browse-menu-item\">\n                        <a href=\"#\" class=\"forum-nav-browse-title\">Target</a>\n                        <ul class=\"forum-nav-browse-submenu\">\n                            <li\n                                class=\"forum-nav-browse-menu-item\"\n                                data-discussion-id=\"child\"\n                                data-cohorted=\"false\"\n                            >\n                                <a href=\"#\" class=\"forum-nav-browse-title\">Child</a>\n                            </li>\n                        </ul>\n                    <li\n                        class=\"forum-nav-browse-menu-item\"\n                        data-discussion-id=\"sibling\"\n                        data-cohorted=\"false\"\n                    >\n                        <a href=\"#\" class=\"forum-nav-browse-title\">Sibling</a>\n                    </li>\n                </ul>\n            </li>\n            <li\n                class=\"forum-nav-browse-menu-item\"\n                data-discussion-id=\"other\"\n                data-cohorted=\"true\"\n            >\n                <a href=\"#\" class=\"forum-nav-browse-title\">Other Category</a>\n            </li>\n        </ul>\n    </div>\n    <div class=\"forum-nav-thread-list-wrapper\" id=\"sort-filter-wrapper\" tabindex=\"-1\">\n        <div class=\"forum-nav-refine-bar\">\n            <label class=\"forum-nav-filter-main\">\n                <select class=\"forum-nav-filter-main-control\">\n                    <option value=\"all\">Show all</option>\n                    <option value=\"unread\">Unread</option>\n                    <option value=\"unanswered\">Unanswered</option>\n                    <option value=\"flagged\">Flagged</option>\n                </select>\n            </label>\n            <% if (isCohorted && isPrivilegedUser) { %>\n            <label class=\"forum-nav-filter-cohort\">\n                <span class=\"sr\">Cohort:</span>\n                <select class=\"forum-nav-filter-cohort-control\">\n                    <option value=\"\">in all cohorts</option>\n                    <option value=\"1\">Cohort1</option>\n                    <option value=\"2\">Cohort2</option>\n                </select>\n            </label>\n            <% } %>\n            <label class=\"forum-nav-sort\">\n                <select class=\"forum-nav-sort-control\">\n                    <option value=\"activity\">by recent activity</option>\n                    <option value=\"comments\">by most activity</option>\n                    <option value=\"votes\">by most votes</option>\n                </select>\n            </label>\n        </div>\n    </div>\n    <div class=\"search-alerts\"></div>\n    <ul class=\"forum-nav-thread-list\"></ul>\n</script>");
            /* jshint +W101 */
            this.threads = [
                DiscussionViewSpecHelper.makeThreadWithProps({
                    id: "1",
                    title: "Thread1",
                    votes: {
                        up_count: '20'
                    },
                    pinned: true,
                    comments_count: 1,
                    created_at: '2013-04-03T20:08:39Z'
                }), DiscussionViewSpecHelper.makeThreadWithProps({
                    id: "2",
                    title: "Thread2",
                    votes: {
                        up_count: '42'
                    },
                    comments_count: 2,
                    created_at: '2013-04-03T20:07:39Z'
                }), DiscussionViewSpecHelper.makeThreadWithProps({
                    id: "3",
                    title: "Thread3",
                    votes: {
                        up_count: '12'
                    },
                    comments_count: 3,
                    created_at: '2013-04-03T20:06:39Z'
                }), DiscussionViewSpecHelper.makeThreadWithProps({
                    id: "4",
                    title: "Thread4",
                    votes: {
                        up_count: '25'
                    },
                    comments_count: 0,
                    pinned: true,
                    created_at: '2013-04-03T20:05:39Z'
                })
            ];
            deferred = $.Deferred();
            spyOn($, "ajax").and.returnValue(deferred);
            this.discussion = new Discussion([]);
            this.view = new DiscussionThreadListView({
                collection: this.discussion,
                el: $("#fixture-element"),
                courseSettings: new DiscussionCourseSettings({
                    is_cohorted: true
                })
            });
            return this.view.render();
        });
        setupAjax = function(callback) {
            return $.ajax.and.callFake(function(params) {
                if (callback) {
                    callback(params);
                }
                params.success({
                    discussion_data: [],
                    page: 1,
                    num_pages: 1
                });
                return {
                    always: function() {
                    }
                };
            });
        };
        renderSingleThreadWithProps = function(props) {
            return makeView(new Discussion([new Thread(DiscussionViewSpecHelper.makeThreadWithProps(props))])).render();
        };
        makeView = function(discussion) {
            return new DiscussionThreadListView({
                el: $("#fixture-element"),
                collection: discussion,
                courseSettings: new DiscussionCourseSettings({
                    is_cohorted: true
                })
            });
        };
        expectFilter = function(filterVal) {
            return $.ajax.and.callFake(function(params) {
                _.each(["unread", "unanswered", "flagged"], function(paramName) {
                    if (paramName === filterVal) {
                        return expect(params.data[paramName]).toEqual(true);
                    } else {
                        return expect(params.data[paramName]).toBeUndefined();
                    }
                });
                return {
                    always: function() {
                    }
                };
            });
        };

        describe("should filter correctly", function() {
            return _.each(["all", "unread", "unanswered", "flagged"], function(filterVal) {
                it("for " + filterVal, function() {
                    expectFilter(filterVal);
                    this.view.$(".forum-nav-filter-main-control").val(filterVal).change();
                    return expect($.ajax).toHaveBeenCalled();
                });
            });
        });

        describe("cohort selector", function() {
            it("should not be visible to students", function() {
                return expect(this.view.$(".forum-nav-filter-cohort-control:visible")).not.toExist();
            });
            it("should allow moderators to select visibility", function() {
                var expectedGroupId,
                    self = this;
                DiscussionSpecHelper.makeModerator();
                this.view.render();
                expectedGroupId = null;
                setupAjax(function(params) {
                    return expect(params.data.group_id).toEqual(expectedGroupId);
                });
                return _.each([
                    {
                        val: "",
                        expectedGroupId: void 0
                    }, {
                        val: "1",
                        expectedGroupId: "1"
                    }, {
                        val: "2",
                        expectedGroupId: "2"
                    }
                ], function(optionInfo) {
                    expectedGroupId = optionInfo.expectedGroupId;
                    self.view.$(".forum-nav-filter-cohort-control").val(optionInfo.val).change();
                    expect($.ajax).toHaveBeenCalled();
                    return $.ajax.calls.reset();
                });
            });
        });

        it("search should clear filter", function() {
            expectFilter(null);
            this.view.$(".forum-nav-filter-main-control").val("flagged");
            this.view.searchFor("foobar");
            return expect(this.view.$(".forum-nav-filter-main-control").val()).toEqual("all");
        });

        checkThreadsOrdering = function(view, sort_order, type) {
            expect(view.$el.find(".forum-nav-thread").children().length).toEqual(4);
            expect(view.$el.find(".forum-nav-thread:nth-child(1) .forum-nav-thread-title").text())
                .toEqual(sort_order[0]);
            expect(view.$el.find(".forum-nav-thread:nth-child(2) .forum-nav-thread-title").text())
                .toEqual(sort_order[1]);
            expect(view.$el.find(".forum-nav-thread:nth-child(3) .forum-nav-thread-title").text())
                .toEqual(sort_order[2]);
            expect(view.$el.find(".forum-nav-thread:nth-child(4) .forum-nav-thread-title").text())
                .toEqual(sort_order[3]);
            return expect(view.$el.find(".forum-nav-sort-control").val()).toEqual(type);
        };

        describe("thread rendering should be correct", function() {
            var checkRender;
            checkRender = function(threads, type, sort_order) {
                var discussion, view;
                discussion = new Discussion(_.map(threads, function(thread) {
                    return new Thread(thread);
                }), {
                    pages: 1,
                    sort: type
                });
                view = makeView(discussion);
                view.render();
                checkThreadsOrdering(view, sort_order, type);
                expect(view.$el.find(".forum-nav-thread-comments-count:visible").length)
                    .toEqual(type === "votes" ? 0 : 4);
                expect(view.$el.find(".forum-nav-thread-votes-count:visible").length)
                    .toEqual(type === "votes" ? 4 : 0);
                if (type === "votes") {
                    return expect(_.map(view.$el.find(".forum-nav-thread-votes-count"), function(element) {
                        return $(element).text().trim();
                    })).toEqual(["+25 votes", "+20 votes", "+42 votes", "+12 votes"]);
                }
            };

            it("with sort preference activity", function() {
                return checkRender(this.threads, "activity", ["Thread1", "Thread2", "Thread3", "Thread4"]);
            });

            it("with sort preference votes", function() {
                return checkRender(this.threads, "votes", ["Thread4", "Thread1", "Thread2", "Thread3"]);
            });

            it("with sort preference comments", function() {
                return checkRender(this.threads, "comments", ["Thread1", "Thread4", "Thread3", "Thread2"]);
            });
        });

        describe("Sort change should be correct", function() {
            var changeSorting;
            changeSorting = function(threads, selected_type, new_type, sort_order) {
                var discussion, sortControl, sorted_threads, view;
                discussion = new Discussion(_.map(threads, function(thread) {
                    return new Thread(thread);
                }), {
                    pages: 1,
                    sort: selected_type
                });
                view = makeView(discussion);
                view.render();
                sortControl = view.$el.find(".forum-nav-sort-control");
                expect(sortControl.val()).toEqual(selected_type);
                sorted_threads = [];
                if (new_type === 'activity') {
                    sorted_threads = [threads[0], threads[3], threads[1], threads[2]];
                } else if (new_type === 'comments') {
                    sorted_threads = [threads[0], threads[3], threads[2], threads[1]];
                } else if (new_type === 'votes') {
                    sorted_threads = [threads[3], threads[0], threads[1], threads[2]];
                }
                $.ajax.and.callFake(function(params) {
                    params.success({
                        "discussion_data": sorted_threads,
                        page: 1,
                        num_pages: 1
                    });
                    return {
                        always: function() {
                        }
                    };
                });
                sortControl.val(new_type).change();
                expect($.ajax).toHaveBeenCalled();
                checkThreadsOrdering(view, sort_order, new_type);
            };

            it("with sort preference activity", function() {
                changeSorting(
                    this.threads, "comments", "activity", ["Thread1", "Thread4", "Thread3", "Thread2"]
                );
            });

            it("with sort preference votes", function() {
                changeSorting(this.threads, "activity", "votes", ["Thread4", "Thread1", "Thread2", "Thread3"]);
            });

            it("with sort preference comments", function() {
                changeSorting(this.threads, "votes", "comments", ["Thread1", "Thread4", "Thread3", "Thread2"]);
            });
        });
        describe("search alerts", function() {
            var testAlertMessages;

            testAlertMessages = function(expectedMessages) {
                return expect($(".search-alert .message").map(function() {
                    return $(this).html();
                }).get()).toEqual(expectedMessages);
            };

            it("renders and removes search alerts", function() {
                var bar, foo;
                testAlertMessages([]);
                foo = this.view.addSearchAlert("foo");
                testAlertMessages(["foo"]);
                bar = this.view.addSearchAlert("bar");
                testAlertMessages(["foo", "bar"]);
                this.view.removeSearchAlert(foo.cid);
                testAlertMessages(["bar"]);
                this.view.removeSearchAlert(bar.cid);
                return testAlertMessages([]);
            });

            it("clears all search alerts", function() {
                this.view.addSearchAlert("foo");
                this.view.addSearchAlert("bar");
                this.view.addSearchAlert("baz");
                testAlertMessages(["foo", "bar", "baz"]);
                this.view.clearSearchAlerts();
                return testAlertMessages([]);
            });
        });

        describe("search spell correction", function() {
            var testCorrection;

            beforeEach(function() {
                return spyOn(this.view, "searchForUser");
            });

            testCorrection = function(view, correctedText) {
                spyOn(view, "addSearchAlert");
                $.ajax.and.callFake(function(params) {
                    params.success({
                        discussion_data: [],
                        page: 42,
                        num_pages: 99,
                        corrected_text: correctedText
                    }, 'success');
                    return {
                        always: function() {
                        }
                    };
                });
                view.searchFor("dummy");
                return expect($.ajax).toHaveBeenCalled();
            };

            it("adds a search alert when an alternate term was searched", function() {
                testCorrection(this.view, "foo");
                expect(this.view.addSearchAlert.calls.count()).toEqual(1);
                return expect(this.view.addSearchAlert.calls.mostRecent().args[0]).toMatch(/foo/);
            });

            it("does not add a search alert when no alternate term was searched", function() {
                testCorrection(this.view, null);
                expect(this.view.addSearchAlert.calls.count()).toEqual(1);
                return expect(this.view.addSearchAlert.calls.mostRecent().args[0]).toMatch(/no threads matched/i);
            });

            it("clears search alerts when a new search is performed", function() {
                spyOn(this.view, "clearSearchAlerts");
                spyOn(DiscussionUtil, "safeAjax");
                this.view.searchFor("dummy");
                return expect(this.view.clearSearchAlerts).toHaveBeenCalled();
            });

            it("clears search alerts when the underlying collection changes", function() {
                spyOn(this.view, "clearSearchAlerts");
                spyOn(this.view, "renderThread");
                this.view.collection.trigger("change", new Thread({
                    id: 1
                }));
                return expect(this.view.clearSearchAlerts).toHaveBeenCalled();
            });
        });

        describe("Search events", function() {
            it("perform search when enter pressed inside search textfield", function() {
                setupAjax();
                spyOn(this.view, "searchFor");
                this.view.$el.find(".forum-nav-search-input").trigger($.Event("keydown", {
                    which: 13
                }));
                return expect(this.view.searchFor).toHaveBeenCalled();
            });

            it("perform search when search icon is clicked", function() {
                setupAjax();
                spyOn(this.view, "searchFor");
                this.view.$el.find(".fa-search").click();
                return expect(this.view.searchFor).toHaveBeenCalled();
            });
        });

        describe("username search", function() {
            var setAjaxResults;

            it("makes correct ajax calls", function() {
                $.ajax.and.callFake(function(params) {
                    expect(params.data.username).toEqual("testing-username");
                    expect(params.url.path()).toEqual(DiscussionUtil.urlFor("users"));
                    params.success({
                        users: []
                    }, 'success');
                    return {
                        always: function() {
                        }
                    };
                });
                this.view.searchForUser("testing-username");
                return expect($.ajax).toHaveBeenCalled();
            });

            setAjaxResults = function(threadSuccess, userResult) {
                return $.ajax.and.callFake(function(params) {
                    if (params.data.text && threadSuccess) {
                        params.success({
                            discussion_data: [],
                            page: 42,
                            num_pages: 99,
                            corrected_text: "dummy"
                        }, "success");
                    } else if (params.data.username) {
                        params.success({
                            users: userResult
                        }, "success");
                    }
                    return {
                        always: function() {
                        }
                    };
                });
            };

            it("gets called after a thread search succeeds", function() {
                spyOn(this.view, "searchForUser").and.callThrough();
                setAjaxResults(true, []);
                this.view.searchFor("gizmo");
                expect(this.view.searchForUser).toHaveBeenCalled();
                return expect($.ajax.calls.mostRecent().args[0].data.username).toEqual("gizmo");
            });

            it("does not get called after a thread search fails", function() {
                spyOn(this.view, "searchForUser").and.callThrough();
                setAjaxResults(false, []);
                this.view.searchFor("gizmo");
                return expect(this.view.searchForUser).not.toHaveBeenCalled();
            });

            it("adds a search alert when an username was matched", function() {
                spyOn(this.view, "addSearchAlert");
                setAjaxResults(true, [
                    {
                        username: "gizmo",
                        id: "1"
                    }
                ]);
                this.view.searchForUser("dummy");
                expect($.ajax).toHaveBeenCalled();
                expect(this.view.addSearchAlert).toHaveBeenCalled();
                return expect(this.view.addSearchAlert.calls.mostRecent().args[0]).toMatch(/gizmo/);
            });

            it("does not add a search alert when no username was matched", function() {
                spyOn(this.view, "addSearchAlert");
                setAjaxResults(true, []);
                this.view.searchForUser("dummy");
                expect($.ajax).toHaveBeenCalled();
                return expect(this.view.addSearchAlert).not.toHaveBeenCalled();
            });
        });

        describe("post type renders correctly", function() {
            it("for discussion", function() {
                renderSingleThreadWithProps({
                    thread_type: "discussion"
                });
                expect($(".forum-nav-thread-wrapper-0 .icon")).toHaveClass("fa-comments");
                return expect($(".forum-nav-thread-wrapper-0 .sr")).toHaveText("discussion");
            });

            it("for answered question", function() {
                renderSingleThreadWithProps({
                    thread_type: "question",
                    endorsed: true
                });
                expect($(".forum-nav-thread-wrapper-0 .icon")).toHaveClass("fa-check-square-o");
                return expect($(".forum-nav-thread-wrapper-0 .sr")).toHaveText("answered question");
            });

            it("for unanswered question", function() {
                renderSingleThreadWithProps({
                    thread_type: "question",
                    endorsed: false
                });
                expect($(".forum-nav-thread-wrapper-0 .icon")).toHaveClass("fa-question");
                return expect($(".forum-nav-thread-wrapper-0 .sr")).toHaveText("unanswered question");
            });
        });

        describe("post labels render correctly", function() {
            beforeEach(function() {
                this.moderatorId = "42";
                this.administratorId = "43";
                this.communityTaId = "44";
                return DiscussionUtil.loadRoles({
                    "Moderator": [parseInt(this.moderatorId)],
                    "Administrator": [parseInt(this.administratorId)],
                    "Community TA": [parseInt(this.communityTaId)]
                });
            });

            it("for pinned", function() {
                renderSingleThreadWithProps({
                    pinned: true
                });
                return expect($(".post-label-pinned").length).toEqual(1);
            });

            it("for following", function() {
                renderSingleThreadWithProps({
                    subscribed: true
                });
                return expect($(".post-label-following").length).toEqual(1);
            });

            it("for moderator", function() {
                renderSingleThreadWithProps({
                    user_id: this.moderatorId
                });
                return expect($(".post-label-by-staff").length).toEqual(1);
            });

            it("for administrator", function() {
                renderSingleThreadWithProps({
                    user_id: this.administratorId
                });
                return expect($(".post-label-by-staff").length).toEqual(1);
            });

            it("for community TA", function() {
                renderSingleThreadWithProps({
                    user_id: this.communityTaId
                });
                return expect($(".post-label-by-community-ta").length).toEqual(1);
            });

            it("when none should be present", function() {
                renderSingleThreadWithProps({});
                return expect($(".forum-nav-thread-labels").length).toEqual(0);
            });
        });

        describe("browse menu", function() {
            var expectBrowseMenuVisible;
            afterEach(function() {
                return $("body").unbind("click");
            });

            expectBrowseMenuVisible = function(isVisible) {
                expect($(".forum-nav-browse-menu:visible").length).toEqual(isVisible ? 1 : 0);
                return expect($(".forum-nav-thread-list-wrapper:visible").length).toEqual(isVisible ? 0 : 1);
            };

            it("should not be visible by default", function() {
                return expectBrowseMenuVisible(false);
            });

            it("should show when header button is clicked", function() {
                $(".forum-nav-browse").click();
                return expectBrowseMenuVisible(true);
            });

            describe("when shown", function() {
                beforeEach(function() {
                    return $(".forum-nav-browse").click();
                });

                it("should hide when header button is clicked", function() {
                    $(".forum-nav-browse").click();
                    return expectBrowseMenuVisible(false);
                });

                it("should hide when a click outside the menu occurs", function() {
                    $(".forum-nav-search-input").click();
                    return expectBrowseMenuVisible(false);
                });

                it("should hide when a search is executed", function() {
                    setupAjax();
                    $(".forum-nav-search-input").trigger($.Event("keydown", {
                        which: 13
                    }));
                    return expectBrowseMenuVisible(false);
                });

                it("should hide when a category is clicked", function() {
                    $(".forum-nav-browse-title")[0].click();
                    return expectBrowseMenuVisible(false);
                });

                it("should still be shown when filter input is clicked", function() {
                    $(".forum-nav-browse-filter-input").click();
                    return expectBrowseMenuVisible(true);
                });

                describe("filtering", function() {
                    var checkFilter;
                    checkFilter = function(filterText, expectedItems) {
                        var visibleItems;
                        $(".forum-nav-browse-filter-input").val(filterText).keyup();
                        visibleItems = $(".forum-nav-browse-title:visible").map(function(i, elem) {
                            return $(elem).text();
                        }).get();
                        return expect(visibleItems).toEqual(expectedItems);
                    };

                    it("should be case-insensitive", function() {
                        return checkFilter("other", ["Other Category"]);
                    });

                    it("should match partial words", function() {
                        return checkFilter("ateg", ["Other Category"]);
                    });

                    it("should show ancestors and descendants of matches", function() {
                        return checkFilter("Target", ["Parent", "Target", "Child"]);
                    });

                    it("should handle multiple words regardless of order", function() {
                        return checkFilter("Following Posts", ["Posts I'm Following"]);
                    });

                    it("should handle multiple words in different depths", function() {
                        return checkFilter("Parent Child", ["Parent", "Target", "Child"]);
                    });
                });
            });

            describe("selecting an item", function() {
                var testSelectionRequest;

                it("should clear the search box", function() {
                    setupAjax();
                    $(".forum-nav-search-input").val("foobar");
                    $(".forum-nav-browse-menu-following .forum-nav-browse-title").click();
                    return expect($(".forum-nav-search-input").val()).toEqual("");
                });

                it("should change the button text", function() {
                    setupAjax();
                    $(".forum-nav-browse-menu-following .forum-nav-browse-title").click();
                    return expect($(".forum-nav-browse-current").text()).toEqual("Posts I'm Following");
                });

                it("should show/hide the cohort selector", function() {
                    var self = this;
                    DiscussionSpecHelper.makeModerator();
                    this.view.render();
                    setupAjax();
                    return _.each([
                        {
                            selector: ".forum-nav-browse-menu-all",
                            cohortVisibility: true
                        }, {
                            selector: ".forum-nav-browse-menu-following",
                            cohortVisibility: false
                        }, {
                            selector:   ".forum-nav-browse-menu-item:" +
                                        "has(.forum-nav-browse-menu-item .forum-nav-browse-menu-item)",
                            cohortVisibility: false
                        }, {
                            selector: "[data-discussion-id=child]",
                            cohortVisibility: false
                        }, {
                            selector: "[data-discussion-id=other]",
                            cohortVisibility: true
                        }
                    ], function(itemInfo) {
                        self.view.$("" + itemInfo.selector + " > .forum-nav-browse-title").click();
                        return expect(self.view.$(".forum-nav-filter-cohort").is(":visible"))
                            .toEqual(itemInfo.cohortVisibility);
                    });
                });

                testSelectionRequest = function(callback, itemText) {
                    setupAjax(callback);
                    $(".forum-nav-browse-title:contains(" + itemText + ")").click();
                    return expect($.ajax).toHaveBeenCalled();
                };

                it("should get all discussions", function() {
                    return testSelectionRequest(function(params) {
                        return expect(params.url.path()).toEqual(DiscussionUtil.urlFor("threads"));
                    }, "All");
                });

                it("should get followed threads", function() {
                    testSelectionRequest(function(params) {
                        return expect(params.url.path())
                            .toEqual(DiscussionUtil.urlFor("followed_threads", window.user.id));
                    }, "Following");
                    return expect($.ajax.calls.mostRecent().args[0].data.group_id).toBeUndefined();
                });

                it("should get threads for the selected leaf", function() {
                    return testSelectionRequest(function(params) {
                        expect(params.url.path()).toEqual(DiscussionUtil.urlFor("search"));
                        return expect(params.data.commentable_ids).toEqual("child");
                    }, "Child");
                });

                it("should get threads for children of the selected intermediate node", function() {
                    return testSelectionRequest(function(params) {
                        expect(params.url.path()).toEqual(DiscussionUtil.urlFor("search"));
                        return expect(params.data.commentable_ids).toEqual("child,sibling");
                    }, "Parent");
                });
            });
        });
    });
}).call(this);
