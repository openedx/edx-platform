define(['backbone', 'jquery', 'underscore',
        'js/spec/student_profile/helpers',
        'js/student_profile/views/badge_view'
    ],
    function(Backbone, $, _, LearnerProfileHelpers, BadgeView) {
        'use strict';
        describe('edx.user.BadgeView', function() {
            var view, badge;

            var createView = function(ownProfile) {
                badge = LearnerProfileHelpers.makeBadge(1);
                var options = {
                    'model': new Backbone.Model(badge),
                    'ownProfile': ownProfile,
                    'badgeMeta': {}
                };
                var view = new BadgeView(options);
                view.render();
                $('body').append(view.$el);
                view.$el.show();
                expect(view.$el.is(':visible')).toBe(true);
                return view;
            };

            afterEach(function() {
                view.$el.remove();
                $('.badges-modal').remove();
            });

            it('profile of other has no share button', function() {
                view = createView(false);
                expect(view.context.ownProfile).toBeFalsy();
                expect(view.$el.find('button.share-button').length).toBe(0);
            });

            it('own profile has share button', function() {
                view = createView(true);
                expect(view.context.ownProfile).toBeTruthy();
                expect(view.$el.find('button.share-button').length).toBe(1);
            });

            it('click on share button calls createModal function', function() {
                view = createView(true);
                spyOn(view, 'createModal');
                view.delegateEvents();
                expect(view.context.ownProfile).toBeTruthy();
                var shareButton = view.$el.find('button.share-button');
                expect(shareButton.length).toBe(1);
                expect(view.createModal).not.toHaveBeenCalled();
                shareButton.click();
                expect(view.createModal).toHaveBeenCalled();
            });

            it('click on share button calls shows the dialog', function(done) {
                view = createView(true);
                expect(view.context.ownProfile).toBeTruthy();
                var shareButton = view.$el.find('button.share-button');
                expect(shareButton.length).toBe(1);
                var modalElement = $('.badges-modal');
                expect(modalElement.length).toBe(0);
                expect(modalElement.is(':visible')).toBeFalsy();
                shareButton.click();
                // Note: this element should have appeared in the dom during: shareButton.click();
                modalElement = $('.badges-modal');
                jasmine.waitUntil(function() {
                    return modalElement.is(':visible');
                }).always(done);
            });

            var testBadgeNameIsDisplayed = function(ownProfile) {
                view = createView(ownProfile);
                var badgeDiv = view.$el.find('.badge-name');
                expect(badgeDiv.length).toBeTruthy();
                expect(badgeDiv.is(':visible')).toBe(true);
                expect(_.count(badgeDiv.html(), badge.badge_class.display_name)).toBeTruthy();
            };

            it('test badge name is displayed for own profile', function() {
                testBadgeNameIsDisplayed(true);
            });

            it('test badge name is displayed for other profile', function() {
                testBadgeNameIsDisplayed(false);
            });

            var testBadgeIconIsDisplayed = function(ownProfile) {
                view = createView(ownProfile);
                var badgeImg = view.$el.find('img.badge');
                expect(badgeImg.length).toBe(1);
                expect(badgeImg.attr('src')).toEqual(badge.image_url);
            };

            it('test badge icon is displayed for own profile', function() {
                testBadgeIconIsDisplayed(true);
            });

            it('test badge icon is displayed for other profile', function() {
                testBadgeIconIsDisplayed(false);
            });
        });
    }
);
