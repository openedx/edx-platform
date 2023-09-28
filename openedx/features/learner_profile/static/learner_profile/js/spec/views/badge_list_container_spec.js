define([
    'backbone',
    'jquery',
    'underscore',
    'URI',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'edx-ui-toolkit/js/pagination/paging-collection',
    'learner_profile/js/spec_helpers/helpers',
    'learner_profile/js/views/badge_list_container'
],
function(Backbone, $, _, URI, AjaxHelpers, PagingCollection, LearnerProfileHelpers, BadgeListContainer) {
    'use strict';

    describe('edx.user.BadgeListContainer', function() {
        var view;

        var createView = function(requests, pageNum, badgeListObject) {
            var BadgeCollection = PagingCollection.extend({
                queryParams: {
                    currentPage: 'current_page'
                }
            });
            var badgeCollection = new BadgeCollection();
            var models = [];
            var badgeListContainer;
            var request;
            var path;
            badgeCollection.url = '/api/badges/v1/assertions/user/staff/';
            _.each(_.range(badgeListObject.count), function(idx) {
                models.push(LearnerProfileHelpers.makeBadge(idx));
            });
            badgeListObject.results = models; // eslint-disable-line no-param-reassign
            badgeCollection.setPage(pageNum);
            request = AjaxHelpers.currentRequest(requests);
            path = new URI(request.url).path();
            expect(path).toBe('/api/badges/v1/assertions/user/staff/');
            AjaxHelpers.respondWithJson(requests, badgeListObject);
            badgeListContainer = new BadgeListContainer({
                collection: badgeCollection

            });
            badgeListContainer.render();
            return badgeListContainer;
        };

        afterEach(function() {
            view.$el.remove();
        });

        it('displays all badges', function() {
            var requests = AjaxHelpers.requests(this),
                badges;
            view = createView(requests, 1, {
                count: 30,
                previous: '/arbitrary/url',
                num_pages: 3,
                next: null,
                start: 20,
                current_page: 1,
                results: []
            });
            badges = view.$el.find('div.badge-display');
            expect(badges.length).toBe(30);
        });

        it('displays placeholder on last page', function() {
            var requests = AjaxHelpers.requests(this),
                placeholder;
            view = createView(requests, 3, {
                count: 30,
                previous: '/arbitrary/url',
                num_pages: 3,
                next: null,
                start: 20,
                current_page: 3,
                results: []
            });
            placeholder = view.$el.find('span.accomplishment-placeholder');
            expect(placeholder.length).toBe(1);
        });

        it('does not display placeholder on first page', function() {
            var requests = AjaxHelpers.requests(this),
                placeholder;
            view = createView(requests, 1, {
                count: 30,
                previous: '/arbitrary/url',
                num_pages: 3,
                next: null,
                start: 0,
                current_page: 1,
                results: []
            });
            placeholder = view.$el.find('span.accomplishment-placeholder');
            expect(placeholder.length).toBe(0);
        });
    });
}
);
