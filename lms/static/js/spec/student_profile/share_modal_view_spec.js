define(['backbone', 'jquery', 'underscore', 'moment',
        'js/spec/student_account/helpers',
        'js/spec/student_profile/helpers',
        'js/student_profile/views/share_modal_view',
        'jquery.simulate'
    ],
    function (Backbone, $, _, Moment, Helpers, LearnerProfileHelpers, ShareModalView) {
        "use strict";
        describe("edx.user.ShareModalView", function () {
            var keys = $.simulate.keyCode;

            var view;

            var createModalView = function () {
                var badge = LearnerProfileHelpers.makeBadge(1);
                var context = _.extend(badge, {
                    'created': new Moment(badge.created),
                    'ownProfile': true,
                    'badgeMeta': {}
                });
                return new ShareModalView({
                    model: new Backbone.Model(context),
                    shareButton: $("<button/>")
                });
            };

            beforeEach(function () {
                view = createModalView();
                // Attach view to document, otherwise click won't work
                view.render();
                $('body').append(view.$el);
                view.$el.show();
                expect(view.$el.is(':visible')).toBe(true);
            });

            afterEach(function () {
                view.$el.remove();
            });

            it("modal view closes on escape", function () {
                spyOn(view, "close");
                view.delegateEvents();
                expect(view.close).not.toHaveBeenCalled();
                $(view.$el).simulate("keydown", {keyCode: keys.ESCAPE});
                expect(view.close).toHaveBeenCalled();
            });

            it("modal view closes click on close", function () {
                spyOn(view, "close");
                view.delegateEvents();
                var $closeButton = view.$el.find("button.close");
                expect($closeButton.length).toBe(1);
                expect(view.close).not.toHaveBeenCalled();
                $closeButton.trigger('click');
                expect(view.close).toHaveBeenCalled();
            });

        });
    }
);
