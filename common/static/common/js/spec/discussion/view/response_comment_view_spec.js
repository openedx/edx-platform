/* globals DiscussionSpecHelper, DiscussionUtil, ResponseCommentView, ResponseCommentShowView, user */
(function() {
    'use strict';
    var $$course_id = '$$course_id';

    describe('ResponseCommentView', function() {
        beforeEach(function() {
            DiscussionSpecHelper.setUpGlobals();
            this.comment = new Comment({
                id: '01234567',
                user_id: user.id,
                course_id: $$course_id,
                body: 'this is a response',
                created_at: '2013-04-03T20:08:39Z',
                abuse_flaggers: ['123'],
                roles: ['Student']
            });
            DiscussionSpecHelper.setUnderscoreFixtures();
            this.view = new ResponseCommentView({
                model: this.comment,
                el: $('#fixture-element')
            });
            spyOn(ResponseCommentShowView.prototype, 'convertMath');
            spyOn(DiscussionUtil, 'makeWmdEditor');
            return this.view.render();
        });
        describe('_delete', function() {
            var setAjaxResult;
            beforeEach(function() {
                this.comment.updateInfo({
                    ability: {
                        can_delete: true
                    }
                });
                this.event = DiscussionSpecHelper.makeEventSpy();
                this.event.target = $('body');
                spyOn(this.comment, 'remove');
                spyOn(this.view.$el, 'remove');
                $(this.event.target).prop('disabled', false);
            });
            setAjaxResult = function(isSuccess) {
                return spyOn($, 'ajax').and.callFake(function(params) {
                    (isSuccess ? params.success : params.error)({});
                    return {
                        always: function() {
                        }
                    };
                });
            };
            it('requires confirmation before deleting', function() {
                spyOn(window, 'confirm').and.returnValue(false);
                setAjaxResult(true);
                this.view._delete(this.event);
                expect(window.confirm).toHaveBeenCalled();
                expect($.ajax).not.toHaveBeenCalled();
                return expect(this.comment.remove).not.toHaveBeenCalled();
            });
            it('removes the deleted comment object', function() {
                setAjaxResult(true);
                this.view._delete(this.event);
                expect(this.comment.remove).toHaveBeenCalled();
                return expect(this.view.$el.remove).toHaveBeenCalled();
            });
            it('calls the ajax comment deletion endpoint', function() {
                setAjaxResult(true);
                this.view._delete(this.event);
                expect(this.event.preventDefault).toHaveBeenCalled();
                expect($.ajax).toHaveBeenCalled();
                return expect($.ajax.calls.mostRecent().args[0].url._parts.path)
                    .toEqual('/courses/edX/999/test/discussion/comments/01234567/delete');
            });
            it('handles ajax errors', function() {
                spyOn(DiscussionUtil, 'discussionAlert');
                setAjaxResult(false);
                this.view._delete(this.event);
                expect(this.event.preventDefault).toHaveBeenCalled();
                expect($.ajax).toHaveBeenCalled();
                expect(this.comment.remove).not.toHaveBeenCalled();
                expect(this.view.$el.remove).not.toHaveBeenCalled();
                return expect(DiscussionUtil.discussionAlert).toHaveBeenCalled();
            });
            it('does not delete a comment if the permission is false', function() {
                this.comment.updateInfo({
                    ability: {
                        'can_delete': false
                    }
                });
                spyOn(window, 'confirm');
                setAjaxResult(true);
                this.view._delete(this.event);
                expect(window.confirm).not.toHaveBeenCalled();
                expect($.ajax).not.toHaveBeenCalled();
                expect(this.comment.remove).not.toHaveBeenCalled();
                return expect(this.view.$el.remove).not.toHaveBeenCalled();
            });
        });
        describe('renderShowView', function() {
            it('renders the show view, removes the edit view, and registers event handlers', function() {
                spyOn(this.view, '_delete');
                spyOn(this.view, 'edit');
                this.view.renderEditView();
                this.view.renderShowView();
                this.view.showView.trigger('comment:_delete', DiscussionSpecHelper.makeEventSpy());
                expect(this.view._delete).toHaveBeenCalled();
                this.view.showView.trigger('comment:edit', DiscussionSpecHelper.makeEventSpy());
                expect(this.view.edit).toHaveBeenCalled();
                return expect(this.view.$('.edit-post-form#comment_' + this.comment.id))
                    .not.toHaveClass('edit-post-form');
            });
        });
        describe('renderEditView', function() {
            it('renders the edit view, removes the show view, and registers event handlers', function() {
                spyOn(this.view, 'update');
                spyOn(this.view, 'cancelEdit');
                this.view.renderEditView();
                this.view.editView.trigger('comment:update', DiscussionSpecHelper.makeEventSpy());
                expect(this.view.update).toHaveBeenCalled();
                this.view.editView.trigger('comment:cancel_edit', DiscussionSpecHelper.makeEventSpy());
                expect(this.view.cancelEdit).toHaveBeenCalled();
                return expect(this.view.$('.edit-post-form#comment_' + this.comment.id)).toHaveClass('edit-post-form');
            });
        });
        describe('edit', function() {
            it('triggers the appropriate event and switches to the edit view', function() {
                var editTarget;
                spyOn(this.view, 'renderEditView');
                editTarget = jasmine.createSpy();
                this.view.bind('comment:edit', editTarget);
                this.view.edit();
                expect(this.view.renderEditView).toHaveBeenCalled();
                return expect(editTarget).toHaveBeenCalled();
            });
        });
        describe('with edit view displayed', function() {
            beforeEach(function() {
                return this.view.renderEditView();
            });
            describe('cancelEdit', function() {
                it('triggers the appropriate event and switches to the show view', function() {
                    var cancelEditTarget;
                    spyOn(this.view, 'renderShowView');
                    cancelEditTarget = jasmine.createSpy();
                    this.view.bind('comment:cancel_edit', cancelEditTarget);
                    this.view.cancelEdit();
                    expect(this.view.renderShowView).toHaveBeenCalled();
                    return expect(cancelEditTarget).toHaveBeenCalled();
                });
            });
            describe('update', function() {
                beforeEach(function() {
                    var self = this;
                    this.updatedBody = 'updated body';
                    this.view.$el.find('.edit-comment-body').html($('<textarea></textarea>'));
                    this.view.$el.find('.edit-comment-body textarea').val(this.updatedBody);
                    spyOn(this.view, 'cancelEdit');
                    spyOn($, 'ajax').and.callFake(function(params) {
                        if (self.ajaxSucceed) {
                            params.success();
                        } else {
                            params.error({
                                status: 500
                            });
                        }
                        return {
                            always: function() {
                            }
                        };
                    });

                    this.event = DiscussionSpecHelper.makeEventSpy();
                    // All the way down in discussion/utils.js there's this line
                    // element.after(...);
                    // element is event.target in this case. This causes a JS exception, so we override the target
                    this.event.target = $('body');
                    $(this.event.target).prop('disabled', false);
                });
                it('calls the update endpoint correctly and displays the show view on success', function() {
                    this.ajaxSucceed = true;
                    this.view.update(this.event);
                    expect($.ajax).toHaveBeenCalled();
                    expect($.ajax.calls.mostRecent().args[0].url._parts.path)
                        .toEqual('/courses/edX/999/test/discussion/comments/01234567/update');
                    expect($.ajax.calls.mostRecent().args[0].data.body).toEqual(this.updatedBody);
                    expect(this.view.model.get('body')).toEqual(this.updatedBody);
                    return expect(this.view.cancelEdit).toHaveBeenCalled();
                });
                it('handles AJAX errors', function() {
                    var originalBody;
                    originalBody = this.comment.get('body');
                    this.ajaxSucceed = false;
                    this.view.update(this.event);
                    expect($.ajax).toHaveBeenCalled();
                    expect($.ajax.calls.mostRecent().args[0].url._parts.path)
                        .toEqual('/courses/edX/999/test/discussion/comments/01234567/update');
                    expect($.ajax.calls.mostRecent().args[0].data.body).toEqual(this.updatedBody);
                    expect(this.view.model.get('body')).toEqual(originalBody);
                    expect(this.view.cancelEdit).not.toHaveBeenCalled();
                    return expect(this.view.$('.edit-comment-form-errors > *').length).toEqual(1);
                });
            });
        });
    });
}).call(this);
