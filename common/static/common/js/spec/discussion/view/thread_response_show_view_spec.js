/* globals DiscussionViewSpecHelper, DiscussionSpecHelper, DiscussionUtil, Thread, ThreadResponseShowView */
(function() {
    'use strict';
    describe('ThreadResponseShowView', function() {
        beforeEach(function() {
            DiscussionSpecHelper.setUpGlobals();
            DiscussionSpecHelper.setUnderscoreFixtures();
            this.user = DiscussionUtil.getUser();
            this.thread = new Thread({
                'thread_type': 'discussion'
            });
            this.commentData = {
                id: 'dummy',
                user_id: '567',
                course_id: 'TestOrg/TestCourse/TestRun',
                body: 'this is a comment',
                created_at: '2013-04-03T20:08:39Z',
                endorsed: false,
                endorsement: {},
                abuse_flaggers: [],
                votes: {
                    up_count: 42
                },
                type: 'comment'
            };
            this.comment = new Comment(this.commentData);
            this.comment.set('thread', this.thread);
            this.view = new ThreadResponseShowView({
                model: this.comment,
                $el: $('#fixture-element')
            });
            spyOn(ThreadResponseShowView.prototype, 'convertMath');
            return this.view.render();
        });
        describe('voting', function() {
            it('renders the vote state correctly', function() {
                return DiscussionViewSpecHelper.checkRenderVote(this.view, this.comment);
            });
            it('check the vote classes after renders', function() {
                return DiscussionViewSpecHelper.checkVoteClasses(this.view);
            });
            it('votes correctly via click', function() {
                return DiscussionViewSpecHelper.checkUpvote(this.view, this.comment, this.user, $.Event('click'));
            });
            it('votes correctly via spacebar', function() {
                return DiscussionViewSpecHelper.checkUpvote(this.view, this.comment, this.user, $.Event('keydown', {
                    which: 32
                }));
            });
            it('unvotes correctly via click', function() {
                return DiscussionViewSpecHelper.checkUnvote(this.view, this.comment, this.user, $.Event('click'));
            });
            it('unvotes correctly via spacebar', function() {
                return DiscussionViewSpecHelper.checkUnvote(this.view, this.comment, this.user, $.Event('keydown', {
                    which: 32
                }));
            });
        });
        it('renders endorsement correctly for a marked answer in a question thread', function() {
            var endorsement;
            endorsement = {
                'username': 'test_endorser',
                'user_id': 'test_id',
                'time': new Date().toISOString()
            };
            this.thread.set('thread_type', 'question');
            this.comment.set({
                'endorsed': true,
                'endorsement': endorsement
            });
            this.view.render();
            expect(this.view.$('.posted-details').text().replace(/\s+/g, ' '))
                .toMatch('marked as answer less than a minute ago by ' + endorsement.username);
            return expect(this.view.$('.posted-details > a').attr('href'))
                .toEqual('/courses/edX/999/test/discussion/forum/users/test_id');
        });
        it('renders anonymous endorsement correctly for a marked answer in a question thread', function() {
            var endorsement;
            endorsement = {
                'username': null,
                'time': new Date().toISOString()
            };
            this.thread.set('thread_type', 'question');
            this.comment.set({
                'endorsed': true,
                'endorsement': endorsement
            });
            this.view.render();
            expect(this.view.$('.posted-details').text()).toMatch('marked as answer less than a minute ago');
            return expect(this.view.$('.posted-details').text()).not.toMatch('\sby\s');
        });
        it('renders endorsement correctly for an endorsed response in a discussion thread', function() {
            var endorsement;
            endorsement = {
                'username': 'test_endorser',
                'user_id': 'test_id',
                'time': new Date().toISOString()
            };
            this.thread.set('thread_type', 'discussion');
            this.comment.set({
                'endorsed': true,
                'endorsement': endorsement
            });
            this.view.render();
            expect(this.view.$('.posted-details').text().replace(/\s+/g, ' '))
                .toMatch('endorsed less than a minute ago by ' + endorsement.username);
            return expect(this.view.$('.posted-details > a').attr('href'))
                .toEqual('/courses/edX/999/test/discussion/forum/users/test_id');
        });
        it('renders anonymous endorsement correctly for an endorsed response in a discussion thread', function() {
            var endorsement;
            endorsement = {
                'username': null,
                'time': new Date().toISOString()
            };
            this.thread.set('thread_type', 'discussion');
            this.comment.set({
                'endorsed': true,
                'endorsement': endorsement
            });
            this.view.render();
            expect(this.view.$('.posted-details').text()).toMatch('endorsed less than a minute ago');
            return expect(this.view.$('.posted-details').text()).not.toMatch('\sby\s');
        });
        it('re-renders correctly when endorsement changes', function() {
            spyOn($, 'ajax').and.returnValue($.Deferred());
            DiscussionUtil.loadRoles({
                'Moderator': [parseInt(window.user.id)]
            });
            this.thread.set('thread_type', 'question');
            this.view.render();
            expect(this.view.$('.posted-details').text()).not.toMatch('marked as answer');
            this.view.$('.action-answer').click();
            expect(this.view.$('.posted-details').text()).toMatch('marked as answer');
            this.view.$('.action-answer').click();
            expect(this.view.$('.posted-details').text()).not.toMatch('marked as answer');

            // Previously the endorsement state would revert after a page load due to a bug in the template
            this.view.render();
            expect(this.view.$('.posted-details').text()).not.toMatch('marked as answer');
        });
        it('allows a moderator to mark an answer in a question thread', function() {
            var endorseButton;
            spyOn($, 'ajax').and.returnValue($.Deferred());
            DiscussionUtil.loadRoles({
                'Moderator': [parseInt(window.user.id)]
            });
            this.thread.set({
                'thread_type': 'question',
                'user_id': (parseInt(window.user.id) + 1).toString()
            });
            this.view.render();
            endorseButton = this.view.$('.action-answer');
            expect(endorseButton.length).toEqual(1);
            expect(endorseButton.closest('.actions-item')).not.toHaveClass('is-hidden');
            endorseButton.click();
            return expect(endorseButton).toHaveClass('is-checked');
        });
        it('allows the author of a question thread to mark an answer', function() {
            var endorseButton;
            spyOn($, 'ajax').and.returnValue($.Deferred());
            this.thread.set({
                'thread_type': 'question',
                'user_id': window.user.id
            });
            this.view.render();
            endorseButton = this.view.$('.action-answer');
            expect(endorseButton.length).toEqual(1);
            expect(endorseButton.closest('.actions-item')).not.toHaveClass('is-hidden');
            endorseButton.click();
            return expect(endorseButton).toHaveClass('is-checked');
        });
        it('does not allow the author of a discussion thread to endorse', function() {
            var endorseButton;
            this.thread.set({
                'thread_type': 'discussion',
                'user_id': window.user.id
            });
            this.view.render();
            endorseButton = this.view.$('.action-endorse');
            expect(endorseButton.length).toEqual(1);
            return expect(endorseButton.closest('.actions-item')).toHaveClass('is-hidden');
        });
        it('does not allow a student who is not the author of a question thread to mark an answer', function() {
            var endorseButton;
            this.thread.set({
                'thread_type': 'question',
                'user_id': (parseInt(window.user.id) + 1).toString()
            });
            this.view.render();
            endorseButton = this.view.$('.action-answer');
            expect(endorseButton.length).toEqual(1);
            return expect(endorseButton.closest('.actions-item')).toHaveClass('is-hidden');
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
                expectOneElement(this.view, '.post-label-reported', false);
                this.comment.set('abuse_flaggers', [DiscussionUtil.getUser().id]);
                expectOneElement(this.view, '.post-label-reported');
                this.comment.set('abuse_flaggers', [DiscussionUtil.getUser().id + 1]);
                return expectOneElement(this.view, '.post-label-reported', false);
            });
            it('displays the reported label when appropriate for a flag moderator', function() {
                DiscussionSpecHelper.makeModerator();
                expectOneElement(this.view, '.post-label-reported', false);
                this.comment.set('abuse_flaggers', [DiscussionUtil.getUser().id]);
                expectOneElement(this.view, '.post-label-reported');
                this.comment.set('abuse_flaggers', [DiscussionUtil.getUser().id + 1]);
                return expectOneElement(this.view, '.post-label-reported');
            });
        });
        describe('endorser display', function() {
            var checkUserLink;
            beforeEach(function() {
                this.comment.set('endorsement', {
                    'username': 'test_endorser',
                    'time': new Date().toISOString()
                });
                return spyOn(DiscussionUtil, 'urlFor').and.returnValue('test_endorser_url');
            });
            checkUserLink = function(element, is_ta, is_staff) {
                expect(element.find('.username').length).toEqual(1);
                expect(element.find('.username').text()).toEqual('test_endorser');
                expect(element.find('.username').attr('href')).toEqual('test_endorser_url');
                expect(element.find('.user-label-community-ta').length).toEqual(is_ta ? 1 : 0);
                return expect(element.find('.user-label-staff').length).toEqual(is_staff ? 1 : 0);
            };
            it('renders nothing when the response has not been endorsed', function() {
                this.comment.set('endorsement', null);
                return expect(this.view.getEndorserDisplay()).toBeNull();
            });
            it('renders correctly for a student-endorsed response', function() {
                var $el;
                $el = $('#fixture-element').html(this.view.getEndorserDisplay());
                return checkUserLink($el, false, false);
            });
            it('renders correctly for a community TA-endorsed response', function() {
                var $el;
                spyOn(DiscussionUtil, 'isTA').and.returnValue(true);
                $el = $('#fixture-element').html(this.view.getEndorserDisplay());
                return checkUserLink($el, true, false);
            });
            it('renders correctly for a staff-endorsed response', function() {
                var $el;
                spyOn(DiscussionUtil, 'isStaff').and.returnValue(true);
                $el = $('#fixture-element').html(this.view.getEndorserDisplay());
                return checkUserLink($el, false, true);
            });
        });
    });
}).call(this);
