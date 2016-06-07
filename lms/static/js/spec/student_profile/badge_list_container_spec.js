define([
        'backbone',
        'jquery',
        'underscore',
        'URI',
        'edx-ui-toolkit/js/pagination/paging-collection',
        'common/js/spec_helpers/ajax_helpers',
        'js/spec/student_profile/helpers',
        'js/student_profile/views/badge_list_container'
    ],
    function (Backbone, $, _, URI, PagingCollection, AjaxHelpers, LearnerProfileHelpers, BadgeListContainer) {
        'use strict';
        describe('edx.user.BadgeListContainer', function () {

            var view, requests;

            var createView = function (requests, pageNum, badge_list_object) {
                var BadgeCollection = PagingCollection.extend({
                    queryParams: {
                        currentPage: 'current_page'
                    }
                });
                var badgeCollection = new BadgeCollection();
                badgeCollection.url = '/api/badges/v1/assertions/user/staff/';
                var models = [];
                _.each(_.range(badge_list_object.count), function (idx) {
                    models.push(LearnerProfileHelpers.makeBadge(idx));
                });
                badge_list_object.results = models;
                badgeCollection.setPage(pageNum);
                var request = AjaxHelpers.currentRequest(requests);
                var path = new URI(request.url).path();
                expect(path).toBe('/api/badges/v1/assertions/user/staff/');
                AjaxHelpers.respondWithJson(requests, badge_list_object);
                var badgeListContainer = new BadgeListContainer({
                    'collection': badgeCollection

                });
                badgeListContainer.render();
                return badgeListContainer;
            };

            afterEach(function () {
                view.$el.remove();
            });

            it('displays all badges', function () {
                requests = AjaxHelpers.requests(this);
                view = createView(requests, 1, {
                    count: 30,
                    previous: '/arbitrary/url',
                    num_pages: 3,
                    next: null,
                    start: 20,
                    current_page: 1,
                    results: []
                });
                var badges = view.$el.find('div.badge-display');
                expect(badges.length).toBe(30);
            });

            it('displays placeholder on last page', function () {
                requests = AjaxHelpers.requests(this);
                view = createView(requests, 3, {
                    count: 30,
                    previous: '/arbitrary/url',
                    num_pages: 3,
                    next: null,
                    start: 20,
                    current_page: 3,
                    results: []
                });
                var placeholder = view.$el.find('span.accomplishment-placeholder');
                expect(placeholder.length).toBe(1);
            });

            it('does not display placeholder on first page', function () {
                requests = AjaxHelpers.requests(this);
                view = createView(requests, 1, {
                    count: 30,
                    previous: '/arbitrary/url',
                    num_pages: 3,
                    next: null,
                    start: 0,
                    current_page: 1,
                    results: []
                });
                var placeholder = view.$el.find('span.accomplishment-placeholder');
                expect(placeholder.length).toBe(0);
            });

        });
    }
);

