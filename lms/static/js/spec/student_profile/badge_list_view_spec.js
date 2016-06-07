define([
        'backbone',
        'jquery',
        'underscore',
        'edx-ui-toolkit/js/pagination/paging-collection',
        'js/spec/student_profile/helpers',
        'js/student_profile/views/badge_list_view'
    ],
    function (Backbone, $, _, PagingCollection, LearnerProfileHelpers, BadgeListView) {
        "use strict";
        describe("edx.user.BadgeListView", function () {

            var view;

            var createView = function (badges, pages, page, hasNextPage) {
                var badgeCollection = new PagingCollection();
                badgeCollection.url = "/api/badges/v1/assertions/user/staff/";
                var models = [];
                _.each(badges, function (element) {
                    models.push(new Backbone.Model(element));
                });
                badgeCollection.models = models;
                badgeCollection.length = badges.length;
                badgeCollection.currentPage = page;
                badgeCollection.totalPages = pages;
                badgeCollection.hasNextPage = function () {
                    return hasNextPage;
                };
                var badge_list = new BadgeListView({
                    'collection': badgeCollection

                });
                return badge_list;
            };

            afterEach(function () {
                view.$el.remove();
            });
            
            it("there is a single row if there is only one badge", function () {
                view = createView([LearnerProfileHelpers.makeBadge(1)], 1, 1, false);
                view.render();
                var rows = view.$el.find('div.row');
                expect(rows.length).toBe(1);
            });

            it("accomplishments placeholder is visible on a last page", function () {
                view = createView([LearnerProfileHelpers.makeBadge(1)], 2, 2, false);
                view.render();
                var placeholder = view.$el.find('span.accomplishment-placeholder');
                expect(placeholder.length).toBe(1);
            });

            it("accomplishments placeholder to be not visible on a first page", function () {
                view = createView([LearnerProfileHelpers.makeBadge(1)], 1, 2, true);
                view.render();
                var placeholder = view.$el.find('span.accomplishment-placeholder');
                expect(placeholder.length).toBe(0);
            });

            it("badges are in two columns (checked by counting rows for a known number of badges)", function () {
                var badges = [];
                _.each(_.range(4), function (item) {
                   badges.push(LearnerProfileHelpers.makeBadge(item));
                });
                view = createView(badges, 1, 2, true);
                view.render();
                var placeholder = view.$el.find('span.accomplishment-placeholder');
                expect(placeholder.length).toBe(0);
                var rows = view.$el.find('div.row');
                expect(rows.length).toBe(2);
            });

        });
    }
);

