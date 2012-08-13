describe "CMS.Views.Module", ->
  beforeEach ->
    setFixtures """
      <div id="module" data-id="i4x://mitx/course/html/module" data-type="html">
        <a href="#" class="module-edit">edit</a>
      </div>
      """

  describe "edit", ->
    beforeEach ->
      @view = new CMS.Views.Module(el: $("#module"))
      spyOn(CMS, "replaceView")
      spyOn(CMS.Views, "ModuleEdit")
        .andReturn(@view = jasmine.createSpy("Views.ModuleEdit"))
      spyOn(CMS.Models, "Module")
        .andReturn(@model = jasmine.createSpy("Models.Module"))
      $(".module-edit").click()

    it "replace the main view with ModuleEdit view", ->
      expect(CMS.replaceView).toHaveBeenCalledWith @view
      expect(CMS.Views.ModuleEdit).toHaveBeenCalledWith model: @model
      expect(CMS.Models.Module).toHaveBeenCalledWith
        id: "i4x://mitx/course/html/module"
        type: "html"
