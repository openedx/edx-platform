describe "CMS.Views.ModuleEdit", ->
  beforeEach ->
    @stubModule = jasmine.createSpyObj("Module", ["editUrl", "loadModule"])
    spyOn($.fn, "load")
    setFixtures """
      <div id="module-edit">
        <a href="#" class="save-update">save</a>
        <a href="#" class="cancel">cancel</a>
        <ol>
          <li>
            <a href="#" class="module-edit" data-id="i4x://mitx/course/html/module" data-type="html">submodule</a>
          </li>
        </ol>
      </div>
      """ #"
    CMS.unbind()

  describe "defaults", ->
    it "set the correct tagName", ->
      expect(new CMS.Views.ModuleEdit(model: @stubModule).tagName).toEqual("section")

    it "set the correct className", ->
      expect(new CMS.Views.ModuleEdit(model: @stubModule).className).toEqual("edit-pane")

  describe "view creation", ->
    beforeEach ->
      @stubModule.editUrl.andReturn("/edit_item?id=stub_module")
      new CMS.Views.ModuleEdit(el: $("#module-edit"), model: @stubModule)

    it "load the edit via ajax and pass to the model", ->
      expect($.fn.load).toHaveBeenCalledWith("/edit_item?id=stub_module", jasmine.any(Function))
      if $.fn.load.mostRecentCall
        $.fn.load.mostRecentCall.args[1]()
        expect(@stubModule.loadModule).toHaveBeenCalledWith($("#module-edit").get(0))

  describe "save", ->
    beforeEach ->
      @stubJqXHR = jasmine.createSpy("stubJqXHR")
      @stubJqXHR.success = jasmine.createSpy("stubJqXHR.success").andReturn(@stubJqXHR)
      @stubJqXHR.error = jasmine.createSpy("stubJqXHR.error").andReturn(@stubJqXHR)
      @stubModule.save = jasmine.createSpy("stubModule.save").andReturn(@stubJqXHR)
      new CMS.Views.ModuleEdit(el: $(".module-edit"), model: @stubModule)
      spyOn(window, "alert")
      $(".save-update").click()

    it "call save on the model", ->
      expect(@stubModule.save).toHaveBeenCalled()

    it "alert user on success", ->
      @stubJqXHR.success.mostRecentCall.args[0]()
      expect(window.alert).toHaveBeenCalledWith("Your changes have been saved.")

    it "alert user on error", ->
      @stubJqXHR.error.mostRecentCall.args[0]()
      expect(window.alert).toHaveBeenCalledWith("There was an error saving your changes. Please try again.")

  describe "cancel", ->
    beforeEach ->
      spyOn(CMS, "popView")
      @view = new CMS.Views.ModuleEdit(el: $("#module-edit"), model: @stubModule)
      $(".cancel").click()

    it "pop current view from viewStack", ->
      expect(CMS.popView).toHaveBeenCalled()

  describe "editSubmodule", ->
    beforeEach ->
      @view = new CMS.Views.ModuleEdit(el: $("#module-edit"), model: @stubModule)
      spyOn(CMS, "pushView")
      spyOn(CMS.Views, "ModuleEdit")
        .andReturn(@view = jasmine.createSpy("Views.ModuleEdit"))
      spyOn(CMS.Models, "Module")
        .andReturn(@model = jasmine.createSpy("Models.Module"))
      $(".module-edit").click()

    it "push another module editing view into viewStack", ->
      expect(CMS.pushView).toHaveBeenCalledWith @view
      expect(CMS.Views.ModuleEdit).toHaveBeenCalledWith model: @model
      expect(CMS.Models.Module).toHaveBeenCalledWith
        id: "i4x://mitx/course/html/module"
        type: "html"
