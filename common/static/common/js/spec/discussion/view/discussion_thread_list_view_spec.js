/* globals
    _, Discussion, DiscussionCourseSettings, DiscussionViewSpecHelper, DiscussionSpecHelper,
    DiscussionThreadListView, DiscussionUtil, Thread
*/
(function() {
    'use strict';
    describe('DiscussionThreadListView', function() {
        var checkThreadsOrdering, expectFilter, makeView, renderSingleThreadWithProps, setupAjax;

        beforeEach(function() {
            var deferred;
            DiscussionSpecHelper.setUpGlobals();
            DiscussionSpecHelper.setUnderscoreFixtures();
            appendSetFixtures(
                '<script type="text/template" id="thread-list-template">' +
                '    <div class="forum-nav-header">' +
                '        <button type="button" class="forum-nav-browse" id="forum-nav-browse" aria-haspopup="true">' +
                '            <span class="icon fa fa-bars" aria-hidden="true"></span>' +
                '            <span class="sr">Discussion topics; currently listing: </span>' +
                '            <span class="forum-nav-browse-current">All Discussions</span>' +
                '        </button>' +
                '        <form class="forum-nav-search">' +
                '            <label>' +
                '                <span class="sr">Search all posts</span>' +
                '                <input' +
                '                    class="forum-nav-search-input"' +
                '                    id="forum-nav-search"' +
                '                    type="text"' +
                '                    placeholder="Search all posts"' +
                '                >' +
                '                <span class="icon fa fa-search" aria-hidden="true"></span>' +
                '            </label>' +
                '        </form>' +
                '    </div>' +
                '    <div class="forum-nav-browse-menu-wrapper" style="display: none">' +
                '        <form class="forum-nav-browse-filter">' +
                '            <label>' +
                '                <span class="sr">Filter Topics</span>' +
                '                <input' +
                '                    type="text"' +
                '                    class="forum-nav-browse-filter-input"' +
                '                    placeholder="filter topics"' +
                '                >' +
                '            </label>' +
                '        </form>' +
                '        <ul class="forum-nav-browse-menu">' +
                '            <li class="forum-nav-browse-menu-item forum-nav-browse-menu-all">' +
                '                <a href="#" class="forum-nav-browse-title">All Discussions</a>' +
                '            </li>' +
                '            <li class="forum-nav-browse-menu-item forum-nav-browse-menu-following">' +
                '                <a href="#" class="forum-nav-browse-title">' +
                '                    <span class="icon fa fa-star" aria-hidden="true"></span>' +
                '                    Posts I\'m Following' +
                '                </a>' +
                '            </li>' +
                '            <li class="forum-nav-browse-menu-item">' +
                '                <a href="#" class="forum-nav-browse-title">Parent</a>' +
                '                <ul class="forum-nav-browse-submenu">' +
                '                    <li class="forum-nav-browse-menu-item">' +
                '                        <a href="#" class="forum-nav-browse-title">Target</a>' +
                '                        <ul class="forum-nav-browse-submenu">' +
                '                            <li' +
                '                                class="forum-nav-browse-menu-item"' +
                '                                data-discussion-id="child"' +
                '                                data-cohorted="false"' +
                '                            >' +
                '                                <a href="#" class="forum-nav-browse-title">Child</a>' +
                '                            </li>' +
                '                        </ul>' +
                '                    <li' +
                '                        class="forum-nav-browse-menu-item"' +
                '                        data-discussion-id="sibling"' +
                '                        data-cohorted="false"' +
                '                    >' +
                '                        <a href="#" class="forum-nav-browse-title">Sibling</a>' +
                '                    </li>' +
                '                </ul>' +
                '            </li>' +
                '            <li' +
                '                class="forum-nav-browse-menu-item"' +
                '                data-discussion-id="other"' +
                '                data-cohorted="true"' +
                '            >' +
                '                <a href="#" class="forum-nav-browse-title">Other Category</a>' +
                '            </li>' +
                '        </ul>' +
                '    </div>' +
                '    <div class="forum-nav-thread-list-wrapper" id="sort-filter-wrapper" tabindex="-1">' +
                '        <div class="forum-nav-refine-bar">' +
                '            <label class="forum-nav-filter-main">' +
                '                <select class="forum-nav-filter-main-control">' +
                '                    <option value="all">Show all</option>' +
                '                    <option value="unread">Unread</option>' +
                '                    <option value="unanswered">Unanswered</option>' +
                '                    <option value="flagged">Flagged</option>' +
                '                </select>' +
                '            </label>' +
                '            <% if (isCohorted && isPrivilegedUser) { %>' +
                '            <label class="forum-nav-filter-cohort">' +
                '                <span class="sr">Cohort:</span>' +
                '                <select class="forum-nav-filter-cohort-control">' +
                '                    <option value="">in all cohorts</option>' +
                '                    <option value="1">Cohort1</option>' +
                '                    <option value="2">Cohort2</option>' +
                '                </select>' +
                '            </label>' +
                '            <% } %>' +
                '            <label class="forum-nav-sort">' +
                '                <select class="forum-nav-sort-control">' +
                '                    <option value="activity">by recent activity</option>' +
                '                    <option value="comments">by most activity</option>' +
                '                    <option value="votes">by most votes</option>' +
                '                </select>' +
                '            </label>' +
                '        </div>' +
                '    </div>' +
                '    <div class="search-alerts"></div>' +
                '    <ul class="forum-nav-thread-list"></ul>' +
                '</script>'
            );
            this.threads = [
                DiscussionViewSpecHelper.makeThreadWithProps({
                    id: '1',
                    title: 'Thread1',
                    votes: {
                        up_count: '20'
                    },
                    pinned: true,
                    comments_count: 1,
                    created_at: '2013-04-03T20:08:39Z'
                }), DiscussionViewSpecHelper.makeThreadWithProps({
                    id: '2',
                    title: 'Thread2',
                    votes: {
                        up_count: '42'
                    },
                    comments_count: 2,
                    created_at: '2013-04-03T20:07:39Z'
                }), DiscussionViewSpecHelper.makeThreadWithProps({
                    id: '3',
                    title: 'Thread3',
                    votes: {
                        up_count: '12'
                    },
                    read: true,
                    comments_count: 3,
                    unread_comments_count: 2,
                    created_at: '2013-04-03T20:06:39Z'
                }), DiscussionViewSpecHelper.makeThreadWithProps({
                    id: '4',
                    title: 'Thread4',
                    votes: {
                        up_count: '25'
                    },
                    comments_count: 0,
                    pinned: true,
                    created_at: '2013-04-03T20:05:39Z'
                })
            ];
            deferred = $.Deferred();
            spyOn($, 'ajax').and.returnValue(deferred);
            this.discussion = new Discussion([]);
            this.view = new DiscussionThreadListView({
                collection: this.discussion,
                el: $('#fixture-element'),
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
                el: $('#fixture-element'),
                collection: discussion,
                showThreadPreview: true,
                courseSettings: new DiscussionCourseSettings({
                    is_cohorted: true
                })
            });
        };
        expectFilter = function(filterVal) {
            return $.ajax.and.callFake(function(params) {
                _.each(['unread', 'unanswered', 'flagged'], function(paramName) {
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

        describe('should filter correctly', function() {
            return _.each(['all', 'unread', 'unanswered', 'flagged'], function(filterVal) {
                it('for ' + filterVal, function() {
                    expectFilter(filterVal);
                    this.view.$('.forum-nav-filter-main-control').val(filterVal).change();
                    return expect($.ajax).toHaveBeenCalled();
                });
            });
        });

        describe('cohort selector', function() {
            it('should not be visible to students', function() {
                return expect(this.view.$('.forum-nav-filter-cohort-control:visible')).not.toExist();
            });
            it('should allow moderators to select visibility', function() {
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
                        val: '',
                        expectedGroupId: void 0
                    }, {
                        val: '1',
                        expectedGroupId: '1'
                    }, {
                        val: '2',
                        expectedGroupId: '2'
                    }
                ], function(optionInfo) {
                    expectedGroupId = optionInfo.expectedGroupId;
                    self.view.$('.forum-nav-filter-cohort-control').val(optionInfo.val).change();
                    expect($.ajax).toHaveBeenCalled();
                    return $.ajax.calls.reset();
                });
            });
        });

        it('search should clear filter', function() {
            expectFilter(null);
            this.view.$('.forum-nav-filter-main-control').val('flagged');
            this.view.searchFor('foobar');
            return expect(this.view.$('.forum-nav-filter-main-control').val()).toEqual('all');
        });

        checkThreadsOrdering = function(view, sortOrder, type) {
            expect(view.$el.find('.forum-nav-thread').children().length).toEqual(4);
            expect(view.$el.find('.forum-nav-thread:nth-child(1) .forum-nav-thread-title').text())
                .toEqual(sortOrder[0]);
            expect(view.$el.find('.forum-nav-thread:nth-child(2) .forum-nav-thread-title').text())
                .toEqual(sortOrder[1]);
            expect(view.$el.find('.forum-nav-thread:nth-child(3) .forum-nav-thread-title').text())
                .toEqual(sortOrder[2]);
            expect(view.$el.find('.forum-nav-thread:nth-child(4) .forum-nav-thread-title').text())
                .toEqual(sortOrder[3]);
            return expect(view.$el.find('.forum-nav-sort-control').val()).toEqual(type);
        };

        describe('thread rendering should be correct', function() {
            var checkRender;
            checkRender = function(threads, type, sortOrder) {
                var discussion, view,
                    isOrderedByVotes = type === 'votes';
                discussion = new Discussion(_.map(threads, function(thread) {
                    return new Thread(thread);
                }), {
                    pages: 1,
                    sort: type
                });
                view = makeView(discussion);
                view.render();
                checkThreadsOrdering(view, sortOrder, type);
                expect(view.$el.find('.forum-nav-thread-comments-count:visible').length)
                    .toEqual(isOrderedByVotes ? 0 : 4);
                expect(view.$el.find('.forum-nav-thread-unread-comments-count:visible').length)
                    .toEqual(isOrderedByVotes ? 0 : 1);
                expect(view.$el.find('.forum-nav-thread-votes-count:visible').length)
                    .toEqual(isOrderedByVotes ? 4 : 0);
                if (isOrderedByVotes) {
                    expect(_.map(view.$el.find('.forum-nav-thread-votes-count'), function(element) {
                        return $(element).text().trim();
                    })).toEqual(['+25 votes', '+20 votes', '+42 votes', '+12 votes']);
                } else {
                    expect(view.$el.find('.forum-nav-thread-votes-count:visible').length)
                        .toEqual(0);
                }
            };

            it('with sort preference "activity"', function() {
                checkRender(this.threads, 'activity', ['Thread1', 'Thread2', 'Thread3', 'Thread4']);
            });

            it('with sort preference "votes"', function() {
                checkRender(this.threads, 'votes', ['Thread4', 'Thread1', 'Thread2', 'Thread3']);
            });

            it('with sort preference "comments"', function() {
                checkRender(this.threads, 'comments', ['Thread1', 'Thread4', 'Thread3', 'Thread2']);
            });
        });

        describe('Sort change should be correct', function() {
            var changeSorting;
            changeSorting = function(threads, selectedType, newType, sortOrder) {
                var discussion, sortControl, sortedThreads, view;
                discussion = new Discussion(_.map(threads, function(thread) {
                    return new Thread(thread);
                }), {
                    pages: 1,
                    sort: selectedType
                });
                view = makeView(discussion);
                view.render();
                sortControl = view.$el.find('.forum-nav-sort-control');
                expect(sortControl.val()).toEqual(selectedType);
                sortedThreads = [];
                if (newType === 'activity') {
                    sortedThreads = [threads[0], threads[3], threads[1], threads[2]];
                } else if (newType === 'comments') {
                    sortedThreads = [threads[0], threads[3], threads[2], threads[1]];
                } else if (newType === 'votes') {
                    sortedThreads = [threads[3], threads[0], threads[1], threads[2]];
                }
                $.ajax.and.callFake(function(params) {
                    params.success({
                        discussion_data: sortedThreads,
                        page: 1,
                        num_pages: 1
                    });
                    return {
                        always: function() {
                        }
                    };
                });
                sortControl.val(newType).change();
                expect($.ajax).toHaveBeenCalled();
                checkThreadsOrdering(view, sortOrder, newType);
            };

            it('with sort preference activity', function() {
                changeSorting(
                    this.threads, 'comments', 'activity', ['Thread1', 'Thread4', 'Thread3', 'Thread2']
                );
            });

            it('with sort preference votes', function() {
                changeSorting(this.threads, 'activity', 'votes', ['Thread4', 'Thread1', 'Thread2', 'Thread3']);
            });

            it('with sort preference comments', function() {
                changeSorting(this.threads, 'votes', 'comments', ['Thread1', 'Thread4', 'Thread3', 'Thread2']);
            });
        });

        describe('post type renders correctly', function() {
            it('for discussion', function() {
                renderSingleThreadWithProps({
                    thread_type: 'discussion'
                });
                expect($('.forum-nav-thread-wrapper-0 .icon')).toHaveClass('fa-comments');
                return expect($('.forum-nav-thread-wrapper-0 .sr')).toHaveText('discussion');
            });

            it('for answered question', function() {
                renderSingleThreadWithProps({
                    thread_type: 'question',
                    endorsed: true
                });
                expect($('.forum-nav-thread-wrapper-0 .icon')).toHaveClass('fa-check-square-o');
                return expect($('.forum-nav-thread-wrapper-0 .sr')).toHaveText('answered question');
            });

            it('for unanswered question', function() {
                renderSingleThreadWithProps({
                    thread_type: 'question',
                    endorsed: false
                });
                expect($('.forum-nav-thread-wrapper-0 .icon')).toHaveClass('fa-question');
                return expect($('.forum-nav-thread-wrapper-0 .sr')).toHaveText('unanswered question');
            });
        });

        describe('post labels render correctly', function() {
            beforeEach(function() {
                this.moderatorId = '42';
                this.administratorId = '43';
                this.communityTaId = '44';
                return DiscussionUtil.loadRoles({
                    Moderator: [parseInt(this.moderatorId, 10)],
                    Administrator: [parseInt(this.administratorId, 10)],
                    'Community TA': [parseInt(this.communityTaId, 10)]
                });
            });

            it('for pinned', function() {
                renderSingleThreadWithProps({
                    pinned: true
                });
                return expect($('.post-label-pinned').length).toEqual(1);
            });

            it('for following', function() {
                renderSingleThreadWithProps({
                    subscribed: true
                });
                return expect($('.post-label-following').length).toEqual(1);
            });

            it('for moderator', function() {
                renderSingleThreadWithProps({
                    user_id: this.moderatorId
                });
                return expect($('.post-label-by-staff').length).toEqual(1);
            });

            it('for administrator', function() {
                renderSingleThreadWithProps({
                    user_id: this.administratorId
                });
                return expect($('.post-label-by-staff').length).toEqual(1);
            });

            it('for community TA', function() {
                renderSingleThreadWithProps({
                    user_id: this.communityTaId
                });
                return expect($('.post-label-by-community-ta').length).toEqual(1);
            });

            it('when none should be present', function() {
                renderSingleThreadWithProps({});
                return expect($('.forum-nav-thread-labels').length).toEqual(0);
            });
        });

        describe('search alerts', function() {
            var testAlertMessages, getAlertMessagesAndClasses;

            testAlertMessages = function(expectedMessages) {
                return expect($('.search-alert .message').map(function() {
                    return $(this).html();
                }).get()).toEqual(expectedMessages);
            };

            getAlertMessagesAndClasses = function() {
                return $('.search-alert').map(function() {
                    return {
                        text: $('.message', this).html(),
                        css_class: $(this).attr('class')
                    };
                }).get();
            };

            it('renders and removes search alerts', function() {
                var bar, foo;
                testAlertMessages([]);
                foo = this.view.addSearchAlert('foo');
                testAlertMessages(['foo']);
                bar = this.view.addSearchAlert('bar');
                testAlertMessages(['foo', 'bar']);
                this.view.removeSearchAlert(foo.cid);
                testAlertMessages(['bar']);
                this.view.removeSearchAlert(bar.cid);
                return testAlertMessages([]);
            });

            it('renders search alert with custom class', function() {
                var messages;
                testAlertMessages([]);

                this.view.addSearchAlert('foo', 'custom-class');
                messages = getAlertMessagesAndClasses();
                expect(messages.length).toEqual(1);
                expect(messages[0].text).toEqual('foo');
                expect(messages[0].css_class).toEqual('search-alert custom-class');

                this.view.addSearchAlert('bar', 'other-class');

                messages = getAlertMessagesAndClasses();
                expect(messages.length).toEqual(2);
                expect(messages[0].text).toEqual('foo');
                expect(messages[0].css_class).toEqual('search-alert custom-class');
                expect(messages[1].text).toEqual('bar');
                expect(messages[1].css_class).toEqual('search-alert other-class');
            });


            it('clears all search alerts', function() {
                this.view.addSearchAlert('foo');
                this.view.addSearchAlert('bar');
                this.view.addSearchAlert('baz');
                testAlertMessages(['foo', 'bar', 'baz']);
                this.view.clearSearchAlerts();
                return testAlertMessages([]);
            });
        });

        describe('search spell correction', function() {
            var testCorrection;

            beforeEach(function() {
                return spyOn(this.view, 'searchForUser');
            });

            testCorrection = function(view, correctedText) {
                spyOn(view, 'addSearchAlert');
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
                view.searchFor('dummy');
                return expect($.ajax).toHaveBeenCalled();
            };

            it('adds a search alert when an alternate term was searched', function() {
                testCorrection(this.view, 'foo');
                expect(this.view.addSearchAlert.calls.count()).toEqual(1);
                return expect(this.view.addSearchAlert.calls.mostRecent().args[0]).toMatch(/foo/);
            });

            it('does not add a search alert when no alternate term was searched', function() {
                testCorrection(this.view, null);
                expect(this.view.addSearchAlert.calls.count()).toEqual(1);
                return expect(this.view.addSearchAlert.calls.mostRecent().args[0]).toMatch(/no threads matched/i);
            });

            it('clears search alerts when a new search is performed', function() {
                spyOn(this.view, 'clearSearchAlerts');
                spyOn(DiscussionUtil, 'safeAjax');
                this.view.searchFor('dummy');
                return expect(this.view.clearSearchAlerts).toHaveBeenCalled();
            });

            it('clears search alerts when the underlying collection changes', function() {
                spyOn(this.view, 'clearSearchAlerts');
                spyOn(this.view, 'renderThread');
                this.view.collection.trigger('change', new Thread({
                    id: 1
                }));
                return expect(this.view.clearSearchAlerts).toHaveBeenCalled();
            });
        });

        describe('username search', function() {
            var setAjaxResults;

            it('makes correct ajax calls', function() {
                $.ajax.and.callFake(function(params) {
                    expect(params.data.username).toEqual('testing-username');
                    expect(params.url.path()).toEqual(DiscussionUtil.urlFor('users'));
                    params.success({
                        users: []
                    }, 'success');
                    return {
                        always: function() {
                        }
                    };
                });
                this.view.searchForUser('testing-username');
                return expect($.ajax).toHaveBeenCalled();
            });

            setAjaxResults = function(threadSuccess, userResult) {
                return $.ajax.and.callFake(function(params) {
                    if (params.data.text && threadSuccess) {
                        params.success({
                            discussion_data: [],
                            page: 42,
                            num_pages: 99,
                            corrected_text: 'dummy'
                        }, 'success');
                    } else if (params.data.username) {
                        params.success({
                            users: userResult
                        }, 'success');
                    }
                    return {
                        always: function() {
                        }
                    };
                });
            };

            it('gets called after a thread search succeeds', function() {
                spyOn(this.view, 'searchForUser').and.callThrough();
                setAjaxResults(true, []);
                this.view.searchFor('gizmo');
                expect(this.view.searchForUser).toHaveBeenCalled();
                return expect($.ajax.calls.mostRecent().args[0].data.username).toEqual('gizmo');
            });

            it('does not get called after a thread search fails', function() {
                spyOn(this.view, 'searchForUser').and.callThrough();
                setAjaxResults(false, []);
                this.view.searchFor('gizmo');
                return expect(this.view.searchForUser).not.toHaveBeenCalled();
            });

            it('adds a search alert when an username was matched', function() {
                spyOn(this.view, 'addSearchAlert');
                setAjaxResults(true, [
                    {
                        username: 'gizmo',
                        id: '1'
                    }
                ]);
                this.view.searchForUser('dummy');
                expect($.ajax).toHaveBeenCalled();
                expect(this.view.addSearchAlert).toHaveBeenCalled();
                return expect(this.view.addSearchAlert.calls.mostRecent().args[0]).toMatch(/gizmo/);
            });

            it('does not add a search alert when no username was matched', function() {
                spyOn(this.view, 'addSearchAlert');
                setAjaxResults(true, []);
                this.view.searchForUser('dummy');
                expect($.ajax).toHaveBeenCalled();
                return expect(this.view.addSearchAlert).not.toHaveBeenCalled();
            });
        });

        describe('thread preview body', function() {
            it('should be shown when showThreadPreview is true', function() {
                renderSingleThreadWithProps({
                    thread_type: 'discussion'
                });
                expect($('.thread-preview-body').length).toEqual(1);
            });

            it('should not show image when showThreadPreview is true', function() {
                renderSingleThreadWithProps({
                    thread_type: 'discussion',
                    body: '![customizedImageAltTitle].png'
                });
                expect($('.thread-preview-body').text()).toEqual('');
            });

            it('should not show MathJax when showThreadPreview is true', function() {
                renderSingleThreadWithProps({
                    thread_type: 'discussion',
                    body: '$$x^2 + sqrt(y)$$'
                });
                expect($('.thread-preview-body').text()).toEqual('');
            });

            it('should not be shown when showThreadPreview is false', function() {
                var view,
                    discussion = new Discussion([]),
                    showThreadPreview = false;
                view = makeView(discussion, showThreadPreview);
                view.render();
                expect(view.$el.find('.thread-preview-body').length).toEqual(0);
            });
        });
    });
}).call(this);
