describe "CMS.Views.Alert as base class", ->
  tpl = readFixtures('alert.underscore')

  beforeEach ->
    setFixtures(sandbox({id: "page-alert"}))
    appendSetFixtures($("<script>", {id: "alert-tpl", type: "text/template"}).text(tpl))

    @model = new CMS.Models.ConfirmationMessage({
      "title": "Portal"
      "message": "Welcome to the Aperture Science Computer-Aided Enrichment Center"
    })
    # it will be interesting to see when this.render is called, so lets spy on it
    spyOn(CMS.Views.Alert.prototype, 'render').andCallThrough()

  it "renders on initalize", ->
    view = new CMS.Views.Alert({model: @model})
    expect(view.render).toHaveBeenCalled()

  it "renders the template", ->
    view = new CMS.Views.Alert({model: @model})
    expect(view.$(".action-close")).toBeDefined()
    expect(view.$('.wrapper')).toHaveClass("is-shown")
    text = view.$el.text()
    expect(text).toMatch(/Portal/)
    expect(text).toMatch(/Aperture Science/)

  it "close button sends a .hide() message", ->
    spyOn(CMS.Views.Alert.prototype, 'hide').andCallThrough()

    view = new CMS.Views.Alert({model: @model})
    view.$(".action-close").click()

    expect(CMS.Views.Alert.prototype.hide).toHaveBeenCalled()
    expect(view.$('.wrapper')).not.toHaveClass("is-shown")
    expect(view.$('.wrapper')).toHaveClass("is-hiding")

describe "CMS.Views.Notification", ->
  tpl = readFixtures('notification.underscore')

  beforeEach ->
    setFixtures(sandbox({id: "page-notification"}))
    appendSetFixtures($("<script>", {id: "notification-tpl", type: "text/template"}).text(tpl))

    @model = new CMS.Models.ConfirmationMessage({
      "title": "Portal"
      "message": "Welcome to the Aperture Science Computer-Aided Enrichment Center"
    })

  # for some reason, expect($("body")) blows up the test runner, so this test
  # just exercises the Prompt rather than asserting on anything. Best I can
  # do for now. :(
  it "changes class on body", ->
    # expect($("body")).not.toHaveClass("prompt-is-shown")
    view = new CMS.Views.Prompt({model: @model})
    # expect($("body")).toHaveClass("prompt-is-shown")
    view.hide()
    # expect($("body")).not.toHaveClass("prompt-is-shown")

describe "CMS.Views.Alert click events", ->
  tpl = readFixtures('alert.underscore')

  beforeEach ->
    @model = new CMS.Models.WarningMessage(
      title: "Unsaved",
      message: "Your content is currently unsaved.",
      actions:
        primary:
          text: "Save",
          class: "save-button",
          click: jasmine.createSpy('primaryClick')
        secondary: [{
            text: "Revert",
            class: "cancel-button",
            click: jasmine.createSpy('secondaryClick')
          }]

      )

    setFixtures(sandbox({id: "page-alert"}))
    appendSetFixtures($("<script>", {id: "alert-tpl", type: "text/template"}).text(tpl))
    @view = new CMS.Views.Alert({model: @model})

  it "should trigger the primary event on a primary click", ->
    @view.primaryClick()
    expect(@model.get('actions').primary.click).toHaveBeenCalled()

  it "should trigger the secondary event on a secondary click", ->
    @view.secondaryClick()
    expect(@model.get('actions').secondary[0].click).toHaveBeenCalled()

  it "should apply class to primary action", ->
    expect(@view.$(".action-primary")).toHaveClass("save-button")

  it "should apply class to secondary action", ->
    expect(@view.$(".action-secondary")).toHaveClass("cancel-button")

