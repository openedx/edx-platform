describe "CMS.Views.SystemFeedback", ->
  beforeEach ->
    setFixtures(sandbox({id: "page-notification"}))
    # CMS.Views.SystemFeedback looks for a template on the page when the code
    # is loaded, and even if we set that template on the page using a fixture,
    # CMS.Views.SystemFeedback has already been loaded, and so that template
    # won't be picked up. This is a dirty hack, to load that template into
    # the code after the code has been loaded already.
    CMS.Views.SystemFeedback.prototype.template = _.template """
      <h1><%= title %></h1>
      <p><%= message %></p>
    """

    @model = new CMS.Models.ConfirmationMessage({
      "title": "Portal"
      "message": "Welcome to the Aperture Science Computer-Aided Enrichment Center"
    })
    # it will be interesting to see when this.render is called, so lets spy on it
    spyOn(CMS.Views.SystemFeedback.prototype, 'render').andCallThrough()

  it "renders on initalize", ->
    view = new CMS.Views.Notification({model: @model})
    expect(view.render).toHaveBeenCalled()

  it "renders the template", ->
    view = new CMS.Views.Notification({model: @model})
    text = view.$el.text()
    expect(text).toMatch(/Portal/)
    expect(text).toMatch(/Aperture Science/)

