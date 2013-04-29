describe "CMS.Models.Module", ->
  it "set the correct URL", ->
    expect(new CMS.Models.Module(courseId: 'course_id').url).toEqual("/course_id/save_item")

  it "set the correct default", ->
    expect(new CMS.Models.Module().defaults).toEqual(courseId: null)
