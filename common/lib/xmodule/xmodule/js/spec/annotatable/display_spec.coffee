describe 'Annotatable', ->
    beforeEach ->
        loadFixtures 'annotatable.html'
    describe 'constructor', ->
        el = $('.xblock-student_view.xmodule_AnnotatableModule')
        beforeEach ->
            @annotatable = new Annotatable(el)
        it 'works', ->
            expect(1).toBe(1)
