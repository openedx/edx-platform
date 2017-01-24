/* globals DiscussionSpecHelper, DiscussionThreadShowView, DiscussionUtil, DiscussionViewSpecHelper, Thread */
(function() {
    'use strict';

    var $$course_id = '$$course_id';
    describe('DiscussionThreadShowView', function() {
        beforeEach(function() {
            DiscussionSpecHelper.setUpGlobals({});
            DiscussionSpecHelper.setUnderscoreFixtures();
            this.user = DiscussionUtil.getUser();
            this.threadData = {
                id: 'dummy',
                user_id: this.user.id,
                username: this.user.get('username'),
                course_id: $$course_id,
                title: 'dummy title',
                body: 'this is a thread',
                created_at: '2013-04-03T20:08:39Z',
                abuse_flaggers: [],
                votes: {
                    up_count: 42
                },
                thread_type: 'discussion',
                closed: false,
                pinned: false,
                type: 'thread'
            };
            this.thread = new Thread(this.threadData);
            this.view = new DiscussionThreadShowView({
                model: this.thread
            });
            this.view.setElement($('#fixture-element'));
            return spyOn(this.view, 'convertMath');
        });
        describe('voting', function() {
            it('renders the vote state correctly', function() {
                return DiscussionViewSpecHelper.checkRenderVote(this.view, this.thread);
            });
            it('votes correctly via click', function() {
                return DiscussionViewSpecHelper.checkUpvote(this.view, this.thread, this.user, $.Event('click'));
            });
            it('votes correctly via spacebar', function() {
                return DiscussionViewSpecHelper.checkUpvote(this.view, this.thread, this.user, $.Event('keydown', {
                    which: 32
                }));
            });
            it('unvotes correctly via click', function() {
                return DiscussionViewSpecHelper.checkUnvote(this.view, this.thread, this.user, $.Event('click'));
            });
            it('unvotes correctly via spacebar', function() {
                return DiscussionViewSpecHelper.checkUnvote(this.view, this.thread, this.user, $.Event('keydown', {
                    which: 32
                }));
            });
        });
        describe('pinning', function() {
            var expectPinnedRendered;
            expectPinnedRendered = function(view, model) {
                var button, pinned;
                pinned = model.get('pinned');
                button = view.$el.find('.action-pin');
                expect(button.hasClass('is-checked')).toBe(pinned);
                return expect(button.attr('aria-checked')).toEqual(pinned.toString());
            };
            it('renders the pinned state correctly', function() {
                this.view.render();
                expectPinnedRendered(this.view, this.thread);
                this.thread.set('pinned', false);
                this.view.render();
                expectPinnedRendered(this.view, this.thread);
                this.thread.set('pinned', true);
                this.view.render();
                return expectPinnedRendered(this.view, this.thread);
            });
            it('exposes the pinning control only to authorized users', function() {
                this.thread.updateInfo({
                    ability: {
                        can_openclose: false
                    }
                });
                this.view.render();
                expect(this.view.$el.find('.action-pin').closest('.is-hidden')).toExist();
                this.thread.updateInfo({
                    ability: {
                        can_openclose: true
                    }
                });
                this.view.render();
                return expect(this.view.$el.find('.action-pin').closest('.is-hidden')).not.toExist();
            });
            it('handles events correctly', function() {
                this.view.render();
                return DiscussionViewSpecHelper.checkButtonEvents(this.view, 'togglePin', '.action-pin');
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
            it('displays the closed label when appropriate', function() {
                expectOneElement(this.view, '.post-label-closed', false);
                this.thread.set('closed', true);
                return expectOneElement(this.view, '.post-label-closed');
            });
            it('displays the pinned label when appropriate', function() {
                expectOneElement(this.view, '.post-label-pinned', false);
                this.thread.set('pinned', true);
                return expectOneElement(this.view, '.post-label-pinned');
            });
            it('displays the reported label when appropriate for a non-staff user', function() {
                expectOneElement(this.view, '.post-label-reported', false);
                this.thread.set('abuse_flaggers', [DiscussionUtil.getUser().id]);
                expectOneElement(this.view, '.post-label-reported');
                this.thread.set('abuse_flaggers', [DiscussionUtil.getUser().id + 1]);
                return expectOneElement(this.view, '.post-label-reported', false);
            });
            it('displays the reported label when appropriate for a flag moderator', function() {
                DiscussionSpecHelper.makeModerator();
                expectOneElement(this.view, '.post-label-reported', false);
                this.thread.set('abuse_flaggers', [DiscussionUtil.getUser().id]);
                expectOneElement(this.view, '.post-label-reported');
                this.thread.set('abuse_flaggers', [DiscussionUtil.getUser().id + 1]);
                return expectOneElement(this.view, '.post-label-reported');
            });
        });
        describe('author display', function() {
            var checkUserLink;
            beforeEach(function() {
                return this.thread.set('user_url', 'test_user_url');
            });
            checkUserLink = function(element, is_ta, is_staff) {
                expect(element.find('.username').length).toEqual(1);
                expect(element.find('.username').text()).toEqual('test_user');
                expect(element.find('.username').attr('href')).toEqual('test_user_url');
                expect(element.find('.user-label-community-ta').length).toEqual(is_ta ? 1 : 0);
                return expect(element.find('.user-label-staff').length).toEqual(is_staff ? 1 : 0);
            };
            it('renders correctly for a student-authored thread', function() {
                var $el;
                $el = $('#fixture-element').html(this.view.getAuthorDisplay());
                return checkUserLink($el, false, false);
            });
            it('renders correctly for a community TA-authored thread', function() {
                var $el;
                this.thread.set('community_ta_authored', true);
                $el = $('#fixture-element').html(this.view.getAuthorDisplay());
                return checkUserLink($el, true, false);
            });
            it('renders correctly for a staff-authored thread', function() {
                var $el;
                this.thread.set('staff_authored', true);
                $el = $('#fixture-element').html(this.view.getAuthorDisplay());
                return checkUserLink($el, false, true);
            });
            it('renders correctly for an anonymously-authored thread', function() {
                var $el;
                this.thread.set('username', null);
                $el = $('#fixture-element').html(this.view.getAuthorDisplay());
                expect($el.find('.username').length).toEqual(0);
                return expect($el.text()).toMatch(/^(\s*)anonymous(\s*)$/);
            });
        });
        describe('cohorting', function() {
            it('renders correctly for an uncohorted thread', function() {
                this.view.render();
                return expect(this.view.$('.group-visibility-label').text().trim())
                    .toEqual('This post is visible to everyone.');
            });
            it('renders correctly for a cohorted thread', function() {
                this.thread.set('group_id', '1');
                this.thread.set('group_name', 'Mock Cohort');
                this.view.render();
                return expect(this.view.$('.group-visibility-label').text().trim())
                    .toEqual('This post is visible only to Mock Cohort.');
            });
        });
    });
}).call(this);
