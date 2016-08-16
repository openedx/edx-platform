/* globals DiscussionSpecHelper, DiscussionThreadProfileView, DiscussionUserProfileView, URI, DiscussionUtil */
(function() {
    'use strict';
    describe('DiscussionUserProfileView', function() {
        var makeThreads, makeView;
        beforeEach(function() {
            DiscussionSpecHelper.setUpGlobals();
            DiscussionSpecHelper.setUnderscoreFixtures();
            return spyOn(DiscussionThreadProfileView.prototype, 'render');
        });
        makeThreads = function(numThreads) {
            return _.map(_.range(numThreads), function(i) {
                return {
                    id: i.toString(),
                    body: 'dummy body'
                };
            });
        };
        makeView = function(threads, page, numPages) {
            return new DiscussionUserProfileView({
                collection: threads,
                page: page,
                numPages: numPages
            });
        };
        describe('thread rendering should be correct', function() {
            var checkRender;
            checkRender = function(numThreads) {
                var threads, view;
                threads = makeThreads(numThreads);
                view = makeView(threads, 1, 1);
                expect(view.$('.discussion').children().length).toEqual(numThreads);
                return _.each(threads, function(thread) {
                    return expect(view.$('#thread_' + thread.id).length).toEqual(1);
                });
            };
            it('with no threads', function() {
                return checkRender(0);
            });
            it('with one thread', function() {
                return checkRender(1);
            });
            it('with several threads', function() {
                return checkRender(5);
            });
        });
        describe('pagination rendering should be correct', function() {
            var baseUri, checkRender, pageInfo;
            baseUri = URI(window.location);
            pageInfo = function(page) {
                return {
                    url: baseUri.clone().addSearch('page', page).toString(),
                    number: page
                };
            };
            checkRender = function(params) {
                var get_page_number, paginator, view;
                view = makeView([], params.page, params.numPages);
                paginator = view.$('.discussion-paginator');
                expect(paginator.find('.current-page').text()).toEqual(params.page.toString());
                expect(paginator.find('.first-page').length).toBe(params.first ? 1 : 0);
                expect(paginator.find('.previous-page').length).toBe(params.previous ? 1 : 0);
                expect(paginator.find('.previous-ellipses').length).toBe(params.leftdots ? 1 : 0);
                expect(paginator.find('.next-page').length).toBe(params.next ? 1 : 0);
                expect(paginator.find('.next-ellipses').length).toBe(params.rightdots ? 1 : 0);
                expect(paginator.find('.last-page').length).toBe(params.last ? 1 : 0);
                get_page_number = function(element) {
                    return parseInt($(element).text());
                };
                expect(_.map(paginator.find('.lower-page a'), get_page_number)).toEqual(params.lowPages);
                return expect(_.map(paginator.find('.higher-page a'), get_page_number)).toEqual(params.highPages);
            };
            it('for one page', function() {
                return checkRender({
                    page: 1,
                    numPages: 1,
                    previous: null,
                    first: null,
                    leftdots: false,
                    lowPages: [],
                    highPages: [],
                    rightdots: false,
                    last: null,
                    next: null
                });
            });
            it('for first page of three (max with no last)', function() {
                return checkRender({
                    page: 1,
                    numPages: 3,
                    previous: null,
                    first: null,
                    leftdots: false,
                    lowPages: [],
                    highPages: [2, 3],
                    rightdots: false,
                    last: null,
                    next: 2
                });
            });
            it('for first page of four (has last but no dots)', function() {
                return checkRender({
                    page: 1,
                    numPages: 4,
                    previous: null,
                    first: null,
                    leftdots: false,
                    lowPages: [],
                    highPages: [2, 3],
                    rightdots: false,
                    last: 4,
                    next: 2
                });
            });
            it('for first page of five (has dots)', function() {
                return checkRender({
                    page: 1,
                    numPages: 5,
                    previous: null,
                    first: null,
                    leftdots: false,
                    lowPages: [],
                    highPages: [2, 3],
                    rightdots: true,
                    last: 5,
                    next: 2
                });
            });
            it('for last page of three (max with no first)', function() {
                return checkRender({
                    page: 3,
                    numPages: 3,
                    previous: 2,
                    first: null,
                    leftdots: false,
                    lowPages: [1, 2],
                    highPages: [],
                    rightdots: false,
                    last: null,
                    next: null
                });
            });
            it('for last page of four (has first but no dots)', function() {
                return checkRender({
                    page: 4,
                    numPages: 4,
                    previous: 3,
                    first: 1,
                    leftdots: false,
                    lowPages: [2, 3],
                    highPages: [],
                    rightdots: false,
                    last: null,
                    next: null
                });
            });
            it('for last page of five (has dots)', function() {
                return checkRender({
                    page: 5,
                    numPages: 5,
                    previous: 4,
                    first: 1,
                    leftdots: true,
                    lowPages: [3, 4],
                    highPages: [],
                    rightdots: false,
                    last: null,
                    next: null
                });
            });
            it('for middle page of five (max with no first/last)', function() {
                return checkRender({
                    page: 3,
                    numPages: 5,
                    previous: 2,
                    first: null,
                    leftdots: false,
                    lowPages: [1, 2],
                    highPages: [4, 5],
                    rightdots: false,
                    last: null,
                    next: 4
                });
            });
            it('for middle page of seven (has first/last but no dots)', function() {
                return checkRender({
                    page: 4,
                    numPages: 7,
                    previous: 3,
                    first: 1,
                    leftdots: false,
                    lowPages: [2, 3],
                    highPages: [5, 6],
                    rightdots: false,
                    last: 7,
                    next: 5
                });
            });
            it('for middle page of nine (has dots)', function() {
                return checkRender({
                    page: 5,
                    numPages: 9,
                    previous: 4,
                    first: 1,
                    leftdots: true,
                    lowPages: [3, 4],
                    highPages: [6, 7],
                    rightdots: true,
                    last: 9,
                    next: 6
                });
            });
        });
        describe('pagination interaction', function() {
            beforeEach(function() {
                var deferred;
                this.view = makeView(makeThreads(3), 1, 2);
                deferred = $.Deferred();
                return spyOn($, 'ajax').and.returnValue(deferred);
            });
            it('causes updated rendering', function() {
                $.ajax.and.callFake(function(params) {
                    params.success({
                        discussion_data: [
                            {
                                id: 'on_page_42',
                                body: 'dummy body'
                            }
                        ],
                        page: 42,
                        num_pages: 99
                    });
                    return {
                        always: function() {
                        }
                    };
                });
                this.view.$('.discussion-pagination a').first().click();
                expect(this.view.$('.current-page').text()).toEqual('42');
                return expect(this.view.$('.last-page').text()).toEqual('99');
            });
            it('handles AJAX errors', function() {
                spyOn(DiscussionUtil, 'discussionAlert');
                $.ajax.and.callFake(function(params) {
                    params.error();
                    return {
                        always: function() {
                        }
                    };
                });
                this.view.$('.discussion-pagination a').first().click();
                return expect(DiscussionUtil.discussionAlert).toHaveBeenCalled();
            });
        });
    });
}).call(this);
