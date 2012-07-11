describe "CMS.Views.WeekEdit", ->
  describe "defaults", ->
    it "set the correct tagName", ->
      expect(new CMS.Views.WeekEdit().tagName).toEqual("section")

    it "set the correct className", ->
      expect(new CMS.Views.WeekEdit().className).toEqual("edit-pane")
