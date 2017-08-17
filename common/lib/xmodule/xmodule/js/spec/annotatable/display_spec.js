/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
describe('Annotatable', function() {
    beforeEach(() => loadFixtures('annotatable.html'));
    return describe('constructor', function() {
        const el = $('.xblock-student_view.xmodule_AnnotatableModule');
        beforeEach(function() {
            return this.annotatable = new Annotatable(el);
        });
        return it('works', () => expect(1).toBe(1));
    });
});
