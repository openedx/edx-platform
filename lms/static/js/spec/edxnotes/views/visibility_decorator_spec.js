define([
    'annotator_1.2.9', 'js/edxnotes/views/visibility_decorator',
    'js/spec/edxnotes/helpers', 'js/spec/edxnotes/custom_matchers'
], function(Annotator, VisibilityDecorator, Helpers, customMatchers) {
    'use strict';
    describe('EdxNotes VisibilityDecorator', function() {
        var params = {
            endpoint: '/test_endpoint',
            user: 'a user',
            usageId : 'an usage',
            courseId: 'a course',
            token: Helpers.makeToken(),
            tokenUrl: '/test_token_url'
        };

        beforeEach(function() {
            customMatchers(this);
            loadFixtures('js/fixtures/edxnotes/edxnotes_wrapper.html');
            this.wrapper = document.getElementById('edx-notes-wrapper-123');
        });

        afterEach(function () {
            VisibilityDecorator._setVisibility(null);
            _.invoke(Annotator._instances, 'destroy');
        });

        it('can initialize Notes if it visibility equals True', function() {
            var note = VisibilityDecorator.factory(this.wrapper, params, true);
            expect(note).toEqual(jasmine.any(Annotator));
        });

        it('does not initialize Notes if it visibility equals False', function() {
            var note = VisibilityDecorator.factory(this.wrapper, params, false);
            expect(note).toBeNull();
        });

        it('can disable all notes', function() {
            VisibilityDecorator.factory(this.wrapper, params, true);
            VisibilityDecorator.factory(document.getElementById('edx-notes-wrapper-456'), params, true);

            VisibilityDecorator.disableNotes();
            expect(Annotator._instances).toHaveLength(0);
        });

        it('can enable the note', function() {
            var secondWrapper = document.getElementById('edx-notes-wrapper-456');
            VisibilityDecorator.factory(this.wrapper, params, false);
            VisibilityDecorator.factory(secondWrapper, params, false);

            VisibilityDecorator.enableNote(this.wrapper);
            expect(Annotator._instances).toHaveLength(1);
            VisibilityDecorator.enableNote(secondWrapper);
            expect(Annotator._instances).toHaveLength(2);
        });
    });
});
