describe "CMS.Models.Asset", ->
    beforeEach ->
        CMS.URL.UPDATE_ASSET = "/update_asset/"
        @model = new CMS.Models.Asset({id: "/c4x/id"})

    afterEach ->
        delete CMS.URL.UPDATE_ASSET

    it "should have a url set", ->
        expect(@model.url()).toEqual("/update_asset//c4x/id")

