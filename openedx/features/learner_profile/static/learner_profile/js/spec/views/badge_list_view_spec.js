// eslint-disable-next-line no-undef
define([
    'backbone',
    'jquery',
    'underscore',
    'edx-ui-toolkit/js/pagination/paging-collection',
    'learner_profile/js/spec_helpers/helpers',
    'learner_profile/js/views/badge_list_view'
],
function(Backbone, $, _, PagingCollection, LearnerProfileHelpers, BadgeListView) {
    'use strict';

    describe('edx.user.BadgeListView', function() {
        // eslint-disable-next-line no-var
        var view;

        // eslint-disable-next-line no-var
        var createView = function(badges, pages, page, hasNextPage) {
            // eslint-disable-next-line no-var
            var badgeCollection = new PagingCollection();
            // eslint-disable-next-line no-var
            var models = [];
            // eslint-disable-next-line no-var
            var badgeList;
            badgeCollection.url = '/api/badges/v1/assertions/user/staff/';
            _.each(badges, function(element) {
                models.push(new Backbone.Model(element));
            });
            badgeCollection.models = models;
            badgeCollection.length = badges.length;
            badgeCollection.currentPage = page;
            badgeCollection.totalPages = pages;
            badgeCollection.hasNextPage = function() {
                return hasNextPage;
            };
            badgeList = new BadgeListView({
                collection: badgeCollection

            });
            return badgeList;
        };

        afterEach(function() {
            view.$el.remove();
        });

        it('there is a single row if there is only one badge', function() {
            // eslint-disable-next-line no-var
            var rows;
            view = createView([LearnerProfileHelpers.makeBadge(1)], 1, 1, false);
            view.render();
            rows = view.$el.find('div.row');
            expect(rows.length).toBe(1);
        });

        it('accomplishments placeholder is visible on a last page', function() {
            // eslint-disable-next-line no-var
            var placeholder;
            view = createView([LearnerProfileHelpers.makeBadge(1)], 2, 2, false);
            view.render();
            placeholder = view.$el.find('span.accomplishment-placeholder');
            expect(placeholder.length).toBe(1);
        });

        it('accomplishments placeholder to be not visible on a first page', function() {
            // eslint-disable-next-line no-var
            var placeholder;
            view = createView([LearnerProfileHelpers.makeBadge(1)], 1, 2, true);
            view.render();
            placeholder = view.$el.find('span.accomplishment-placeholder');
            expect(placeholder.length).toBe(0);
        });

        it('badges are in two columns (checked by counting rows for a known number of badges)', function() {
            // eslint-disable-next-line no-var
            var badges = [];
            // eslint-disable-next-line no-var
            var placeholder;
            // eslint-disable-next-line no-var
            var rows;
            _.each(_.range(4), function(item) {
                badges.push(LearnerProfileHelpers.makeBadge(item));
            });
            view = createView(badges, 1, 2, true);
            view.render();
            placeholder = view.$el.find('span.accomplishment-placeholder');
            expect(placeholder.length).toBe(0);
            rows = view.$el.find('div.row');
            expect(rows.length).toBe(2);
        });
    });
}
);
