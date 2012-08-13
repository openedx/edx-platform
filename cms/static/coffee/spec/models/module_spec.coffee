describe "CMS.Models.Module", ->
  it "set the correct URL", ->
    expect(new CMS.Models.Module().url).toEqual("/save_item")

  it "set the correct default", ->
    expect(new CMS.Models.Module().defaults).toEqual({data: ""})

  describe "loadModule", ->
    describe "when the module exists", ->
      beforeEach ->
        @fakeModule = jasmine.createSpy("fakeModuleObject")
        window.FakeModule = jasmine.createSpy("FakeModule").andReturn(@fakeModule)
        @module = new CMS.Models.Module(type: "FakeModule")
        @stubDiv = $('<div />')
        @stubElement = $('<div class="xmodule_edit" />')
        @stubElement.data('type', "FakeModule")

        @stubDiv.append(@stubElement)
        @module.loadModule(@stubDiv)

      afterEach ->
        window.FakeModule = undefined

      it "initialize the module", ->
        expect(window.FakeModule).toHaveBeenCalled()
        # Need to compare underlying nodes, because jquery selectors
        # aren't equal even when they point to the same node.
        # http://stackoverflow.com/questions/9505437/how-to-test-jquery-with-jasmine-for-element-id-if-used-as-this
        expectedNode = @stubElement[0]
        actualNode = window.FakeModule.mostRecentCall.args[0][0]

        expect(actualNode).toEqual(expectedNode)
        expect(@module.module).toEqual(@fakeModule)

    describe "when the module does not exists", ->
      beforeEach ->
        @previousConsole = window.console
        window.console = jasmine.createSpyObj("fakeConsole", ["error"])
        @module = new CMS.Models.Module(type: "HTML")
        @module.loadModule($("<div>"))

      afterEach ->
        window.console = @previousConsole

      it "print out error to log", ->
        expect(window.console.error).toHaveBeenCalled()
        expect(window.console.error.mostRecentCall.args[0]).toMatch("^Unable to load")


  describe "editUrl", ->
    it "construct the correct URL based on id", ->
      expect(new CMS.Models.Module(id: "i4x://mit.edu/module/html_123").editUrl())
        .toEqual("/edit_item?id=i4x%3A%2F%2Fmit.edu%2Fmodule%2Fhtml_123")

  describe "save", ->
    beforeEach ->
      spyOn(Backbone.Model.prototype, "save")
      @module = new CMS.Models.Module()

    describe "when the module exists", ->
      beforeEach ->
        @module.module = jasmine.createSpyObj("FakeModule", ["save"])
        @module.module.save.andReturn("module data")
        @module.save()

      it "set the data and call save on the module", ->
        expect(@module.get("data")).toEqual("\"module data\"")

      it "call save on the backbone model", ->
        expect(Backbone.Model.prototype.save).toHaveBeenCalled()

    describe "when the module does not exists", ->
      beforeEach ->
        @module.save()

      it "call save on the backbone model", ->
        expect(Backbone.Model.prototype.save).toHaveBeenCalled()
