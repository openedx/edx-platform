describe "CMS.Models.Module", ->
  it "set the correct URL", ->
    expect(new CMS.Models.Module().url).toEqual("/save_item")

  it "set the correct default", ->
    expect(new CMS.Models.Module().defaults).toEqual(undefined)
