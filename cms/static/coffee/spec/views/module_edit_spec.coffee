define ["coffee/src/views/module_edit", "js/models/module_info", "xmodule"], (ModuleEdit, ModuleModel) ->

    describe "ModuleEdit", ->
      beforeEach ->
        @stubModule = new ModuleModel
            id: "stub-id"

        setFixtures """
        <li class="component" id="stub-id">
          <div class="component-editor">
            <div class="module-editor">
              ${editor}
            </div>
            <a href="#" class="save-button">Save</a>
            <a href="#" class="cancel-button">Cancel</a>
          </div>
          <div class="component-actions">
            <a href="#" class="edit-button"><span class="edit-icon white"></span>Edit</a>
            <a href="#" class="delete-button"><span class="delete-icon white"></span>Delete</a>
          </div>
          <span class="drag-handle"></span>
          <section class="xblock xblock-student_view xmodule_display xmodule_stub" data-type="StubModule">
            <div id="stub-module-content"/>
          </section>
        </li>
        """
        spyOn($.fn, 'load').andReturn(@moduleData)

        @moduleEdit = new ModuleEdit(
          el: $(".component")
          model: @stubModule
          onDelete: jasmine.createSpy()
        )

      describe "class definition", ->
        it "sets the correct tagName", ->
          expect(@moduleEdit.tagName).toEqual("li")

        it "sets the correct className", ->
          expect(@moduleEdit.className).toEqual("component")

      describe "methods", ->
        describe "initialize", ->
          beforeEach ->
            spyOn(ModuleEdit.prototype, 'render')
            @moduleEdit = new ModuleEdit(
              el: $(".component")
              model: @stubModule
              onDelete: jasmine.createSpy()
            )

          it "renders the module editor", ->
            expect(@moduleEdit.render).toHaveBeenCalled()

        describe "render", ->
          beforeEach ->
            spyOn(@moduleEdit, 'loadDisplay')
            spyOn(@moduleEdit, 'delegateEvents')
            @moduleEdit.render()

          it "loads the module preview and editor via ajax on the view element", ->
            expect(@moduleEdit.$el.load).toHaveBeenCalledWith("/xblock/#{@moduleEdit.model.id}", jasmine.any(Function))
            @moduleEdit.$el.load.mostRecentCall.args[1]()
            expect(@moduleEdit.loadDisplay).toHaveBeenCalled()
            expect(@moduleEdit.delegateEvents).toHaveBeenCalled()

        describe "loadDisplay", ->
          beforeEach ->
            spyOn(XBlock, 'initializeBlock')
            @moduleEdit.loadDisplay()

          it "loads the .xmodule-display inside the module editor", ->
            expect(XBlock.initializeBlock).toHaveBeenCalled()
            expect(XBlock.initializeBlock.mostRecentCall.args[0]).toBe($('.xblock-student_view'))
