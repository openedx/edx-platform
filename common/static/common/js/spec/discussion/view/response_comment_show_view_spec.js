/* globals DiscussionSpecHelper, DiscussionUtil, DiscussionViewSpecHelper, ResponseCommentShowView */
(function() {
    'use strict';
    describe('ResponseCommentShowView', function() {
        beforeEach(function() {
            DiscussionSpecHelper.setUpGlobals();
            DiscussionSpecHelper.setUnderscoreFixtures();
            this.comment = new Comment({
                id: '01234567',
                user_id: '567',
                course_id: 'edX/999/test',
                body: 'this is a response',
                created_at: '2013-04-03T20:08:39Z',
                abuse_flaggers: ['123'],
                roles: []
            });
            this.view = new ResponseCommentShowView({
                model: this.comment
            });
            return spyOn(this.view, 'convertMath');
        });
        it('defines the tag', function() {
            expect($('#jasmine-fixtures')).toExist();
            expect(this.view.tagName).toBeDefined();
            return expect(this.view.el.tagName.toLowerCase()).toBe('li');
        });
        it('is tied to the model', function() {
            return expect(this.view.model).toBeDefined();
        });
        describe('rendering', function() {
            beforeEach(function() {
                return spyOn(this.view, 'renderAttrs');
            });
            it('can be flagged for abuse', function() {
                this.comment.flagAbuse();
                return expect(this.comment.get('abuse_flaggers')).toEqual(['123', '567']);
            });
            it('can be unflagged for abuse', function() {
                var temp_array;
                temp_array = [];
                temp_array.push(window.user.get('id'));
                this.comment.set('abuse_flaggers', temp_array);
                this.comment.unflagAbuse();
                return expect(this.comment.get('abuse_flaggers')).toEqual([]);
            });
        });
        describe('_delete', function() {
            it('triggers on the correct events', function() {
                DiscussionUtil.loadRoles([]);
                this.comment.updateInfo({
                    ability: {
                        can_delete: true
                    }
                });
                this.view.render();
                return DiscussionViewSpecHelper.checkButtonEvents(this.view, '_delete', '.action-delete');
            });
            it('triggers the delete event', function() {
                var triggerTarget;
                triggerTarget = jasmine.createSpy();
                this.view.bind('comment:_delete', triggerTarget);
                this.view._delete();
                return expect(triggerTarget).toHaveBeenCalled();
            });
        });
        describe('edit', function() {
            it('triggers on the correct events', function() {
                DiscussionUtil.loadRoles([]);
                this.comment.updateInfo({
                    ability: {
                        can_edit: true
                    }
                });
                this.view.render();
                return DiscussionViewSpecHelper.checkButtonEvents(this.view, 'edit', '.action-edit');
            });
            it('triggers comment:edit when the edit button is clicked', function() {
                var triggerTarget;
                triggerTarget = jasmine.createSpy();
                this.view.bind('comment:edit', triggerTarget);
                this.view.edit();
                return expect(triggerTarget).toHaveBeenCalled();
            });
        });
        describe('labels', function() {
            var expectOneElement;
            expectOneElement = function(view, selector, visible) {
                var elements;
                if (typeof visible === 'undefined' || visible === null) {
                    visible = true;
                }
                view.render();
                elements = view.$el.find(selector);
                expect(elements.length).toEqual(1);
                if (visible) {
                    return expect(elements).not.toHaveClass('is-hidden');
                } else {
                    return expect(elements).toHaveClass('is-hidden');
                }
            };
            it('displays the reported label when appropriate for a non-staff user', function() {
                this.comment.set('abuse_flaggers', []);
                expectOneElement(this.view, '.post-label-reported', false);
                this.comment.set('abuse_flaggers', [DiscussionUtil.getUser().id]);
                expectOneElement(this.view, '.post-label-reported');
                this.comment.set('abuse_flaggers', [DiscussionUtil.getUser().id + 1]);
                return expectOneElement(this.view, '.post-label-reported', false);
            });
            it('displays the reported label when appropriate for a flag moderator', function() {
                DiscussionSpecHelper.makeModerator();
                this.comment.set('abuse_flaggers', []);
                expectOneElement(this.view, '.post-label-reported', false);
                this.comment.set('abuse_flaggers', [DiscussionUtil.getUser().id]);
                expectOneElement(this.view, '.post-label-reported');
                this.comment.set('abuse_flaggers', [DiscussionUtil.getUser().id + 1]);
                return expectOneElement(this.view, '.post-label-reported');
            });
        });
    });
}).call(this);
