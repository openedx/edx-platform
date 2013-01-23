describe "CMS", ->
  beforeEach ->
    CMS.unbind()

  it "should initialize Models", ->
    expect(CMS.Models).toBeDefined()

  it "should initialize Views", ->
    expect(CMS.Views).toBeDefined()

describe "main helper", ->
  beforeEach ->
    @previousAjaxSettings = $.extend(true, {}, $.ajaxSettings)
    window.stubCookies["csrftoken"] = "stubCSRFToken"
    $(document).ready()

  afterEach ->
    $.ajaxSettings = @previousAjaxSettings

  it "turn on Backbone emulateHTTP", ->
    expect(Backbone.emulateHTTP).toBeTruthy()

  it "setup AJAX CSRF token", ->
    expect($.ajaxSettings.headers["X-CSRFToken"]).toEqual("stubCSRFToken")
