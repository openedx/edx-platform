describe "CMS.Models.Metadata", ->
  it "has no url", ->
    expect(new CMS.Models.Metadata().url).toEqual("/save_item")