/* globals Comments, Content, DiscussionSpecHelper, DiscussionUser, DiscussionUtil, Thread */
(function() {
    'use strict';
    describe('All Content', function() {
        beforeEach(function() {
            return DiscussionSpecHelper.setUpGlobals();
        });
        describe('Staff and TA Content', function() {
            beforeEach(function() {
                return DiscussionUtil.loadRoles({
                    'Moderator': [567],
                    'Administrator': [567],
                    'Community TA': [567]
                });
            });
            it('anonymous thread should not include login role label', function() {
                var anon_content;
                anon_content = new Content();
                anon_content.initialize();
                expect(anon_content.get('staff_authored')).toBe(false);
                return expect(anon_content.get('community_ta_authored')).toBe(false);
            });
            return it('general thread should include login role label', function() {
                var anon_content;
                anon_content = new Content({
                    user_id: '567'
                });
                anon_content.initialize();
                expect(anon_content.get('staff_authored')).toBe(true);
                return expect(anon_content.get('community_ta_authored')).toBe(true);
            });
        });
        describe('Content', function() {
            beforeEach(function() {
                this.content = new Content({
                    id: '01234567',
                    user_id: '567',
                    course_id: 'edX/999/test',
                    body: 'this is some content',
                    abuse_flaggers: ['123']
                });
            });
            it('should exist', function() {
                return expect(Content).toBeDefined();
            });
            it('is initialized correctly', function() {
                this.content.initialize();
                expect(Content.contents['01234567']).toEqual(this.content);
                expect(this.content.get('id')).toEqual('01234567');
                expect(this.content.get('user_url')).toEqual('/courses/edX/999/test/discussion/forum/users/567');
                expect(this.content.get('children')).toEqual([]);
                return expect(this.content.get('comments')).toEqual(jasmine.any(Comments));
            });
            it('can update info', function() {
                this.content.updateInfo({
                    ability: {
                        'can_edit': true
                    },
                    voted: true,
                    subscribed: true
                });
                expect(this.content.get('ability')).toEqual({
                    'can_edit': true
                });
                expect(this.content.get('voted')).toEqual(true);
                return expect(this.content.get('subscribed')).toEqual(true);
            });
            it('can be flagged for abuse', function() {
                this.content.flagAbuse();
                return expect(this.content.get('abuse_flaggers')).toEqual(['123', '567']);
            });
            return it('can be unflagged for abuse', function() {
                var temp_array;
                temp_array = [];
                temp_array.push(window.user.get('id'));
                this.content.set('abuse_flaggers', temp_array);
                this.content.unflagAbuse();
                return expect(this.content.get('abuse_flaggers')).toEqual([]);
            });
        });
        return describe('Comments', function() {
            beforeEach(function() {
                this.comment1 = new Comment({
                    id: '123'
                });
                this.comment2 = new Comment({
                    id: '345'
                });
            });
            it('can contain multiple comments', function() {
                var myComments;
                myComments = new Comments();
                expect(myComments.length).toEqual(0);
                myComments.add(this.comment1);
                expect(myComments.length).toEqual(1);
                myComments.add(this.comment2);
                return expect(myComments.length).toEqual(2);
            });
            it('returns results to the find method', function() {
                var myComments;
                myComments = new Comments();
                myComments.add(this.comment1);
                return expect(myComments.find('123')).toBe(this.comment1);
            });
            return it('can be endorsed', function() {
                DiscussionUtil.loadRoles({
                    'Moderator': [111],
                    'Administrator': [222],
                    'Community TA': [333]
                });
                this.discussionThread = new Thread({
                    id: 1,
                    thread_type: 'discussion',
                    user_id: 99
                });
                this.discussionResponse = new Comment({
                    id: 1,
                    thread: this.discussionThread
                });
                this.questionThread = new Thread({
                    id: 1,
                    thread_type: 'question',
                    user_id: 99
                });
                this.questionResponse = new Comment({
                    id: 1,
                    thread: this.questionThread
                });
                window.user = new DiscussionUser({
                    id: 111
                });
                expect(this.discussionResponse.canBeEndorsed()).toBe(true);
                expect(this.questionResponse.canBeEndorsed()).toBe(true);
                window.user = new DiscussionUser({
                    id: 222
                });
                expect(this.discussionResponse.canBeEndorsed()).toBe(true);
                expect(this.questionResponse.canBeEndorsed()).toBe(true);
                window.user = new DiscussionUser({
                    id: 333
                });
                expect(this.discussionResponse.canBeEndorsed()).toBe(true);
                expect(this.questionResponse.canBeEndorsed()).toBe(true);
                window.user = new DiscussionUser({
                    id: 99
                });
                expect(this.discussionResponse.canBeEndorsed()).toBe(false);
                expect(this.questionResponse.canBeEndorsed()).toBe(true);
                window.user = new DiscussionUser({
                    id: 999
                });
                expect(this.discussionResponse.canBeEndorsed()).toBe(false);
                return expect(this.questionResponse.canBeEndorsed()).toBe(false);
            });
        });
    });
}).call(this);
