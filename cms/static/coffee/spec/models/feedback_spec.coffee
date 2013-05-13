describe "CMS.Models.SystemFeedback", ->
  beforeEach ->
    @model = new CMS.Models.SystemFeedback()

  it "should have an empty message by default", ->
    expect(@model.get("message")).toEqual("")

  it "should have an empty title by default", ->
    expect(@model.get("title")).toEqual("")

  it "should not have a type set by default", ->
    expect(@model.get("type")).toBeNull()

  it "should be shown by default", ->
    expect(@model.get("shown")).toEqual(true)

  it "should trigger a change event on calling .hide()", ->
    spy = jasmine.createSpy()
    @model.on("change", spy)

    @model.hide()

    expect(@model.get("shown")).toEqual(false)
    expect(spy).toHaveBeenCalled()

describe "CMS.Models.WarningMessage", ->
  beforeEach ->
    @model = new CMS.Models.WarningMessage()

  it "should have the correct type", ->
    expect(@model.get("type")).toEqual("warning")

describe "CMS.Models.ErrorMessage", ->
  beforeEach ->
    @model = new CMS.Models.ErrorMessage()

  it "should have the correct type", ->
    expect(@model.get("type")).toEqual("error")

describe "CMS.Models.ConfirmationMessage", ->
  beforeEach ->
    @model = new CMS.Models.ConfirmationMessage()

  it "should have the correct type", ->
    expect(@model.get("type")).toEqual("confirmation")

