describe 'Annotatable', ->
    beforeEach ->
        loadFixtures 'annotatable.html'
    describe 'constructor', ->
        el = $('.xmodule_display.xmodule_AnnotatableModule')
        beforeEach ->
            @annotatable = new Annotatable(el)
        it 'binds module to element', ->
            expect(@annotatable.el).toBe(el)
        it 'initializes toggle states to be false', ->
            toggleStates = ['annotationsHidden', 'instructionsHidden']
            expect(@annotatable[toggleState]).toBeFalsy() for toggleState in toggleStates
        it 'initializes event handlers', ->
            eventHandlers = [ 'onClickToggleAnnotations', 'onClickToggleInstructions', 'onClickReply', 'onCLickReturn']
            expect(@annotatable[eventHandler]).toBeDefined() for handler in handlers
