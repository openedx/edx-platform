describe "TabsEditorDescriptor", ->
  beforeEach ->
    @isInactiveClass = "is-inactive"
    @isCurrent = "current"
    loadFixtures 'tabs-edit.html'
    @descriptor = new TabsEditorDescriptor($('.tabs-edit'))

  describe "constructor", ->
    it "first tab should be visible", ->
      expect(@descriptor.$tabs.first()).toHaveClass(@isCurrent)
      expect(@descriptor.$content.first()).not.toHaveClass(@isInactiveClass)

  describe "onSwitchEditor", ->
    it "switch tabs", ->
      @descriptor.$tabs.eq(1).trigger("click")
      expect(@descriptor.$tabs.eq(0)).not.toHaveClass(@isCurrent)
      expect(@descriptor.$content.eq(0)).toHaveClass(@isInactiveClass)
      expect(@descriptor.$tabs.eq(1)).toHaveClass(@isCurrent)
      expect(@descriptor.$content.eq(1)).not.toHaveClass(@isInactiveClass)

    it "event 'TabsEditor:changeTab' is triggered", ->
      spyOn($.fn, 'trigger').andCallThrough()
      @descriptor.$tabs.eq(1).trigger("click")
      expect($.fn.trigger.mostRecentCall.args[0]).toEqual('TabsEditor:changeTab')
      expect($.fn.trigger.mostRecentCall.args[1]).toEqual(
        [
          'Tab 1', # tab_name
          '#tab-1' # tab_id
        ]
      )

    it "if click on current tab, anything should happens", ->
      spyOn($.fn, 'trigger').andCallThrough()
      currentTab = @descriptor.$tabs.filter('.' + @isCurrent)
      @descriptor.$tabs.eq(0).trigger("click")
      expect(@descriptor.$tabs.filter('.' + @isCurrent)).toEqual(currentTab)
      expect($.fn.trigger.calls.length).toEqual(1)

  describe "save", ->
    it "if CodeMirror exist, data should be retreived", ->
      editBox = $('.edit-box')
      CodeMirrorStub =
        getValue: () ->
           editBox.val()

      editBox.data('CodeMirror', CodeMirrorStub)
      data = @descriptor.save().data
      expect(data).toEqual('Advanced Editor Text')

    it "detach click event", ->
      spyOn($.fn, "off")
      @descriptor.save()
      expect($.fn.off).toHaveBeenCalledWith(
        'click',
        '.editor-tabs .tab',
        @descriptor.onSwitchEditor
      )

  describe "registerTabCallback", ->
    beforeEach ->
      @id = 'id'
      TabsEditorDescriptor.registerTabCallback("#{@id}")

    afterEach ->
      $("#editor-tab-#{@id}").off 'TabsEditor:changeTab'

    it "event subscribed", ->
      expect($("#editor-tab-#{@id}")).toHandle('TabsEditor:changeTab')
