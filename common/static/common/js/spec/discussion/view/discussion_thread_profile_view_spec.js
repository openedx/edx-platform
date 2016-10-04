/* globals Discussion, DiscussionSpecHelper, DiscussionThreadProfileView, Thread */
(function() {
    'use strict';
    describe('DiscussionThreadProfileView', function() {
        var checkBody, checkPostWithImages, makeThread, makeView, spyConvertMath;
        beforeEach(function() {
            DiscussionSpecHelper.setUpGlobals();
            DiscussionSpecHelper.setUnderscoreFixtures();
            this.threadData = {
                id: '1',
                body: 'dummy body',
                discussion: new Discussion(),
                abuse_flaggers: [],
                commentable_id: 'dummy_discussion',
                votes: {
                    up_count: '42'
                },
                created_at: '2014-09-09T20:11:08Z'
            };
            this.imageTag = '<img src="https://www.google.com.pk/images/srpr/logo11w.png">';
        });
        makeView = function(thread) {
            var view;
            view = new DiscussionThreadProfileView({
                model: thread
            });
            spyConvertMath(view);
            return view;
        };
        makeThread = function(threadData) {
            var thread;
            thread = new Thread(threadData);
            thread.discussion = new Discussion();
            return thread;
        };
        spyConvertMath = function(view) {
            return spyOn(view, 'convertMath').and.callFake(function() {
                return this.model.set('markdownBody', this.model.get('body'));
            });
        };
        checkPostWithImages = function(numberOfImages, truncatedText, threadData, imageTag) {
            var expectedHtml, expectedText, i, testText, view, _i, _ref;
            expectedHtml = '<p>';
            threadData.body = '<p>';
            testText = '';
            expectedText = '';
            if (truncatedText) {
                testText = new Array(100).join('test ');
                expectedText = testText.substring(0, 139) + '…';
            } else {
                testText = 'Test body';
                expectedText = 'Test body';
                // I really have no idea what it is supposed to mean - probably just iteration, but better be safe
                for (
                    i = _i = 0, _ref = numberOfImages - 1;
                    0 <= _ref ? _i <= _ref : _i >= _ref;
                    i = 0 <= _ref ? ++_i : --_i
                ) {
                    threadData.body = threadData.body + imageTag;
                    if (i === 0) {
                        expectedHtml = expectedHtml + imageTag;
                    } else {
                        expectedHtml = expectedHtml + '<em>image omitted</em>';
                    }
                }
            }
            threadData.body = threadData.body + '<em>' + testText + '</em></p>';
            if (numberOfImages > 1) {
                expectedHtml = expectedHtml + '<em>' + expectedText +
                    '</em></p><p><em>Some images in this post have been omitted</em></p>';
            } else {
                expectedHtml = expectedHtml + '<em>' + expectedText + '</em></p>';
            }
            view = makeView(makeThread(threadData));
            view.render();
            return expect(view.$el.find('.post-body').html()).toEqual(expectedHtml);
        };
        checkBody = function(truncated, view, threadData) {
            var expectedOutput, inputHtmlStripped, outputHtmlStripped;
            view.render();
            if (!truncated) {
                expect(view.model.get('body')).toEqual(view.model.get('abbreviatedBody'));
                return expect(view.$el.find('.post-body').html()).toEqual(threadData.body);
            } else {
                expect(view.model.get('body')).not.toEqual(view.model.get('abbreviatedBody'));
                expect(view.$el.find('.post-body').html()).not.toEqual(threadData.body);
                outputHtmlStripped = view.$el.find('.post-body').html().replace(/(<([^>]+)>)/ig, '');
                outputHtmlStripped = outputHtmlStripped.replace('Some images in this post have been omitted', '');
                outputHtmlStripped = outputHtmlStripped.replace('image omitted', '');
                inputHtmlStripped = threadData.body.replace(/(<([^>]+)>)/ig, '');
                expectedOutput = inputHtmlStripped.substring(0, 139) + '…';
                expect(outputHtmlStripped).toEqual(expectedOutput);
                return expect(view.$el.find('.post-body').html().indexOf('…')).toBeGreaterThan(0);
            }
        };
        describe('Body markdown should be correct', function() {
            var numImages, truncatedText, _i, _j, _len, _len1, _ref, _ref1;
            it('untruncated text without markdown body', function() {
                var view;
                this.threadData.body = 'Test body';
                view = makeView(makeThread(this.threadData));
                return checkBody(false, view, this.threadData);
            });
            it('truncated text without markdown body', function() {
                var view;
                this.threadData.body = new Array(100).join('test ');
                view = makeView(makeThread(this.threadData));
                return checkBody(true, view, this.threadData);
            });
            it('untruncated text with markdown body', function() {
                var view;
                this.threadData.body = '<p>' + this.imageTag + '<em>Google top search engine</em></p>';
                view = makeView(makeThread(this.threadData));
                return checkBody(false, view, this.threadData);
            });
            it('truncated text with markdown body', function() {
                var testText, view;
                testText = new Array(100).join('test ');
                this.threadData.body = '<p>' + this.imageTag + this.imageTag + '<em>' + testText + '</em></p>';
                view = makeView(makeThread(this.threadData));
                return checkBody(true, view, this.threadData);
            });
            _ref = [1, 2, 10];
            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                numImages = _ref[_i];
                _ref1 = [true, false];
                for (_j = 0, _len1 = _ref1.length; _j < _len1; _j++) {
                    truncatedText = _ref1[_j];
                    it(
                        'body with ' + numImages + ' images and ' + (truncatedText ? 'truncated' : 'untruncated') +
                        ' text',
                        // eslint-disable no-loop-func
                        function() {
                            return checkPostWithImages(numImages, truncatedText, this.threadData, this.imageTag);
                        }
                        // eslint-enable no-loop-func
                    );
                }
            }
            it('check the thread retrieve url', function() {
                var thread;
                thread = makeThread(this.threadData);
                return expect(thread.urlFor('retrieve'))
                    .toBe('/courses/edX/999/test/discussion/forum/dummy_discussion/threads/1');
            });
        });
    });
}).call(this);
