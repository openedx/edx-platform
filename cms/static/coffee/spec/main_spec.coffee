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

describe "AJAX Errors", ->
  tpl = readFixtures('system-feedback.underscore')

  beforeEach ->
    setFixtures($("<script>", {id: "system-feedback-tpl", type: "text/template"}).text(tpl))
    appendSetFixtures(sandbox({id: "page-notification"}))
    @requests = requests = []
    @xhr = sinon.useFakeXMLHttpRequest()
    @xhr.onCreate = (xhr) -> requests.push(xhr)

  afterEach ->
    @xhr.restore()

  it "successful AJAX request does not pop an error notification", ->
    expect($("#page-notification")).toBeEmpty()
    $.ajax("/test")
    expect($("#page-notification")).toBeEmpty()
    @requests[0].respond(200)
    expect($("#page-notification")).toBeEmpty()

  it "AJAX request with error should pop an error notification", ->
    $.ajax("/test")
    @requests[0].respond(500)
    expect($("#page-notification")).not.toBeEmpty()
    expect($("#page-notification")).toContain('div.wrapper-notification-error')

  it "can override AJAX request with error so it does not pop an error notification", ->
    $.ajax
      url: "/test"
      notifyOnError: false
    @requests[0].respond(500)
    expect($("#page-notification")).toBeEmpty()

