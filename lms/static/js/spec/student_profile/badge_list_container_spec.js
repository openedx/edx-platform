define(['backbone', 'jquery', 'underscore', 'URI', 'common/js/spec_helpers/ajax_helpers',
        'js/spec/student_profile/helpers',
        'js/student_profile/views/badge_list_container',
        'common/js/components/collections/paging_collection'
    ],
    function (Backbone, $, _, URI, AjaxHelpers, LearnerProfileHelpers, BadgeListContainer, PagingCollection) {
        'use strict';
        describe('edx.user.BadgeListContainer', function () {

            var view, requests;

            var createView = function (requests, badge_list_object) {
                var badgeCollection = new PagingCollection();
                badgeCollection.url = '/api/badges/v1/assertions/user/staff/';
                var models = [];
                _.each(_.range(badge_list_object.count), function (idx) {
                    models.push(LearnerProfileHelpers.makeBadge(idx));
                });
                badge_list_object.results = models;
                badgeCollection.fetch();
                var request = AjaxHelpers.currentRequest(requests);
                var path = new URI(request.url).path();
                expect(path).toBe('/api/badges/v1/assertions/user/staff/');
                AjaxHelpers.respondWithJson(requests, badge_list_object);
                var badge_list_container = new BadgeListContainer({
                    'collection': badgeCollection

                });
                badge_list_container.render();
                return badge_list_container;
            };

            afterEach(function () {
                view.$el.remove();
            });

            it('displays all badges', function () {
                requests = AjaxHelpers.requests(this);
                view = createView(requests, {
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
                view = createView(requests, {
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
                view = createView(requests, {
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

