xdescribe "ResponseCommentShowView", ->

  it "defines the class", ->
    spyOn myComment, 'initialize'
    myComment = new Comment()
    myView = new ResponseCommentShowView(myComment)
    expect(myView.tagName).toBeDefined()
