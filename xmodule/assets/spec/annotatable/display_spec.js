describe('Annotatable', function() {
    beforeEach(() => loadFixtures('annotatable.html'));
    describe('constructor', function() {
        const el = $('.xblock-student_view.xmodule_AnnotatableModule');
        beforeEach(function() {
            this.annotatable = new Annotatable(el);
        });
        it('works', () => expect(1).toBe(1));
    });
});
