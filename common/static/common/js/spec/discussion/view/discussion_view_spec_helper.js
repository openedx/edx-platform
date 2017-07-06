/* globals DiscussionUtil */
(function() {
    'use strict';
    var __indexOf = [].indexOf || function(item) {
            for (var i = 0, l = this.length; i < l; i++) {
                if (i in this && this[i] === item) {
                    return i;
                }
            }
            return -1;
        };

    this.DiscussionViewSpecHelper = (function() {
        var triggerVoteEvent;

        function DiscussionViewSpecHelper() {
        }

        DiscussionViewSpecHelper.makeThreadWithProps = function(props) {
            var thread;
            thread = {
                id: "dummy_id",
                thread_type: "discussion",
                pinned: false,
                endorsed: false,
                votes: {
                    up_count: '0'
                },
                read: false,
                unread_comments_count: 0,
                comments_count: 0,
                abuse_flaggers: [],
                body: "",
                title: "dummy title",
                created_at: "2014-08-18T01:02:03Z",
                ability: {
                    can_delete: false,
                    can_reply: true,
                    can_vote: false,
                    editable: false
                }
            };
            return $.extend(thread, props);
        };

        DiscussionViewSpecHelper.checkVoteClasses = function(view) {
            var action_button, display_button;
            view.render();
            display_button = view.$el.find(".display-vote");
            expect(display_button.hasClass("is-hidden")).toBe(true);
            action_button = view.$el.find(".action-vote");
            return expect(action_button).not.toHaveAttr('style', 'display: inline; ');
        };

        DiscussionViewSpecHelper.expectVoteRendered = function(view, model, user) {
            var button;
            button = view.$el.find(".action-vote");
            expect(button.hasClass("is-checked")).toBe(user.voted(model));
            expect(button.attr("aria-checked")).toEqual(user.voted(model).toString());
            expect(button.find(".vote-count").text()).toMatch("^" + (model.get('votes').up_count) + " Votes?$");
            return expect(button.find(".sr.js-sr-vote-count").text())
                .toMatch("^there are currently " + (model.get('votes').up_count) + " votes?$");
        };

        DiscussionViewSpecHelper.checkRenderVote = function(view, model) {
            view.render();
            DiscussionViewSpecHelper.expectVoteRendered(view, model, window.user);
            window.user.vote(model);
            view.render();
            DiscussionViewSpecHelper.expectVoteRendered(view, model, window.user);
            window.user.unvote(model);
            view.render();
            return DiscussionViewSpecHelper.expectVoteRendered(view, model, window.user);
        };

        triggerVoteEvent = function(view, event, expectedUrl) {
            var deferred;
            deferred = $.Deferred();
            spyOn($, "ajax").and.callFake(function(params) {
                expect(params.url.toString()).toEqual(expectedUrl);
                return deferred;
            });
            view.render();
            view.$el.find(".action-vote").trigger(event);
            expect($.ajax).toHaveBeenCalled();
            return deferred.resolve();
        };

        DiscussionViewSpecHelper.checkUpvote = function(view, model, user, event) {
            var initialVoteCount, _ref, _ref1;
            expect((_ref = model.id, __indexOf.call(user.get('upvoted_ids'), _ref) >= 0)).toBe(false);
            initialVoteCount = model.get('votes').up_count;
            triggerVoteEvent(view, event, DiscussionUtil.urlFor("upvote_" + (model.get('type')), model.id) + "?ajax=1");
            expect((_ref1 = model.id, __indexOf.call(user.get('upvoted_ids'), _ref1) >= 0)).toBe(true);
            return expect(model.get('votes').up_count).toEqual(initialVoteCount + 1);
        };

        DiscussionViewSpecHelper.checkUnvote = function(view, model, user, event) {
            var initialVoteCount, _ref;
            user.vote(model);
            expect((_ref = model.id, __indexOf.call(user.get('upvoted_ids'), _ref) >= 0)).toBe(true);
            initialVoteCount = model.get('votes').up_count;
            triggerVoteEvent(
                view, event, DiscussionUtil.urlFor("undo_vote_for_" + (model.get('type')), model.id) + "?ajax=1"
            );
            expect(user.get('upvoted_ids')).toEqual([]);
            return expect(model.get('votes').up_count).toEqual(initialVoteCount - 1);
        };

        DiscussionViewSpecHelper.checkButtonEvents = function(view, viewFunc, buttonSelector) {
            var button, spy;
            spy = spyOn(view, viewFunc);
            button = view.$el.find(buttonSelector);
            button.click();
            expect(spy).toHaveBeenCalled();
            spy.calls.reset();
            button.trigger($.Event("keydown", {
                which: 13
            }));
            expect(spy).not.toHaveBeenCalled();
            spy.calls.reset();
            button.trigger($.Event("keydown", {
                which: 32
            }));
            return expect(spy).toHaveBeenCalled();
        };

        DiscussionViewSpecHelper.checkVoteButtonEvents = function(view) {
            return this.checkButtonEvents(view, "toggleVote", ".action-vote");
        };

        DiscussionViewSpecHelper.setNextResponseContent = function(content) {
            return $.ajax.and.callFake(function(params) {
                params.success({
                    "content": content
                });
                return {
                    always: function() {
                    }
                };
            });
        };

        return DiscussionViewSpecHelper;

    })();

}).call(this);
