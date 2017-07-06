/* globals DiscussionSpecHelper, ResponseCommentView, Thread, ThreadResponseView, ThreadResponseShowView */
(function() {
    'use strict';
    describe('ThreadResponseView', function() {
        beforeEach(function() {
            DiscussionSpecHelper.setUpGlobals();
            DiscussionSpecHelper.setUnderscoreFixtures();
            this.thread = new Thread({
                "thread_type": "discussion"
            });
            this.response = new Comment({
                children: [{}, {}],
                thread: this.thread
            });
            this.view = new ThreadResponseView({
                model: this.response,
                el: $("#fixture-element")
            });
            spyOn(ThreadResponseShowView.prototype, "render");
            return spyOn(ResponseCommentView.prototype, "render");
        });
        describe('closed and open Threads', function() {
            var checkCommentForm;
            checkCommentForm = function(closed) {
                var comment, commentData, thread, view;
                thread = new Thread({
                    "thread_type": "discussion",
                    "closed": closed
                });
                commentData = {
                    id: "dummy",
                    user_id: "567",
                    course_id: "TestOrg/TestCourse/TestRun",
                    body: "this is a comment",
                    created_at: "2013-04-03T20:08:39Z",
                    abuse_flaggers: [],
                    type: "comment",
                    children: [],
                    thread: thread
                };
                comment = new Comment(commentData);
                view = new ThreadResponseView({
                    model: comment,
                    el: $("#fixture-element")
                });
                view.render();
                return expect(view.$('.comment-form').closest('li').is(":visible")).toBe(!closed);
            };
            it('hides comment form when thread is closed', function() {
                return checkCommentForm(true);
            });
            it('show comment form when thread is open', function() {
                return checkCommentForm(false);
            });
        });
        describe('renderComments', function() {
            it('hides "show comments" link if collapseComments is not set', function() {
                this.view.render();
                expect(this.view.$(".comments")).toBeVisible();
                return expect(this.view.$(".action-show-comments")).not.toBeVisible();
            });
            it('hides "show comments" link if collapseComments is set but response has no comments', function() {
                this.response = new Comment({
                    children: [],
                    thread: this.thread
                });
                this.view = new ThreadResponseView({
                    model: this.response,
                    el: $("#fixture-element"),
                    collapseComments: true
                });
                this.view.render();
                expect(this.view.$(".comments")).toBeVisible();
                return expect(this.view.$(".action-show-comments")).not.toBeVisible();
            });
            it(
                'hides comments if collapseComments is set and shows them when "show comments" link is clicked',
                function() {
                    this.view = new ThreadResponseView({
                        model: this.response,
                        el: $("#fixture-element"),
                        collapseComments: true
                    });
                    this.view.render();
                    expect(this.view.$(".comments")).not.toBeVisible();
                    expect(this.view.$(".action-show-comments")).toBeVisible();
                    this.view.$(".action-show-comments").click();
                    expect(this.view.$(".comments")).toBeVisible();
                    return expect(this.view.$(".action-show-comments")).not.toBeVisible();
                }
            );
            it('populates commentViews and binds events', function() {
                this.view.createEditView();
                spyOn(this.view, 'cancelEdit');
                spyOn(this.view, 'cancelCommentEdits');
                spyOn(this.view, 'hideCommentForm');
                spyOn(this.view, 'showCommentForm');
                this.view.renderComments();
                expect(this.view.commentViews.length).toEqual(2);
                this.view.commentViews[0].trigger("comment:edit", jasmine.createSpyObj("event", ["preventDefault"]));
                expect(this.view.cancelEdit).toHaveBeenCalled();
                expect(this.view.cancelCommentEdits).toHaveBeenCalled();
                expect(this.view.hideCommentForm).toHaveBeenCalled();
                this.view.commentViews[0].trigger("comment:cancel_edit");
                return expect(this.view.showCommentForm).toHaveBeenCalled();
            });
        });
        describe('cancelCommentEdits', function() {
            it('calls cancelEdit on each comment view', function() {
                this.view.renderComments();
                expect(this.view.commentViews.length).toEqual(2);
                _.each(this.view.commentViews, function(commentView) {
                    return spyOn(commentView, 'cancelEdit');
                });
                this.view.cancelCommentEdits();
                return _.each(this.view.commentViews, function(commentView) {
                    return expect(commentView.cancelEdit).toHaveBeenCalled();
                });
            });
        });
    });

}).call(this);
