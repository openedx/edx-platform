describe "CMS.Models.SystemFeedback", ->
  m = new CMS.Models.SystemFeedback()

  it "should have an empty message by default", ->
    expect(m.get("message")).toEqual("")
