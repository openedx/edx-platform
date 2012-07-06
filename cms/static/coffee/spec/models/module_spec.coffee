describe "CMS.Models.Module", ->
  it "set the correct URL", ->
    expect(new CMS.Models.Module().url).toEqual("/save_item")

  it "set the correct default", ->
    expect(new CMS.Models.Module().defaults).toEqual({data: ''})

  describe "loadModule", ->
    describe "when the module exists", ->
      beforeEach ->
        @fakeModule = jasmine.createSpy("fakeModuleObject")
        window.FakeModule = jasmine.createSpy("FakeModule").andReturn(@fakeModule)
        @module = new CMS.Models.Module(type: "FakeModule")
        @stubElement = $('<div>')
        @module.loadModule(@stubElement)

      afterEach ->
        window.FakeModule = undefined

      it "initialize the module", ->
        expect(window.FakeModule).toHaveBeenCalledWith(@stubElement)
        expect(@module.module).toEqual(@fakeModule)

    describe "when the module does not exists", ->
      beforeEach ->
        @previousConsole = window.console
        window.console = jasmine.createSpyObj("fakeConsole", ["error"])
        @module = new CMS.Models.Module(type: "HTML")
        @module.loadModule($('<div>'))

      afterEach ->
        window.console = @previousConsole

      it "print out error to log", ->
        expect(window.console.error).toHaveBeenCalledWith("Unable to load HTML.")


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
