describe "CMS.Models.SystemFeedback", ->
    beforeEach ->
        @model = new CMS.Models.SystemFeedback()

    it "should have an empty message by default", ->
        expect(@model.get("message")).toEqual("")

    it "should have an empty title by default", ->
        expect(@model.get("title")).toEqual("")

    it "should not have an intent set by default", ->
        expect(@model.get("intent")).toBeNull()


describe "CMS.Models.WarningMessage", ->
    beforeEach ->
        @model = new CMS.Models.WarningMessage()

    it "should have the correct intent", ->
        expect(@model.get("intent")).toEqual("warning")

describe "CMS.Models.ErrorMessage", ->
    beforeEach ->
        @model = new CMS.Models.ErrorMessage()

    it "should have the correct intent", ->
        expect(@model.get("intent")).toEqual("error")

describe "CMS.Models.ConfirmationMessage", ->
    beforeEach ->
        @model = new CMS.Models.ConfirmationMessage()

    it "should have the correct intent", ->
        expect(@model.get("intent")).toEqual("confirmation")
