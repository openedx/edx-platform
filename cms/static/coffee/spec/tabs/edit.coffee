describe "TabsEditorDescriptor", ->
  beforeEach ->
    @isInactiveClass = "is-inactive"
    @isCurrent = "current"
    loadFixtures 'tabs-edit.html'
    @descriptor = new window.TabsEditorDescriptor($('.editor-with-tabs'))
    window.TabsEditorDescriptor['tabs_save_functions'] = {}
    @html_id = 'test_id'
    window.TabsEditorDescriptor['tabs_save_functions'][@html_id] = {}
    window.TabsEditorDescriptor['tabs_save_functions'][@html_id]['Tab 0'] = ->
      'Advanced Editor Text'
    window.TabsEditorDescriptor['tabs_save_functions'][@html_id]['Tab 1'] = ->
      'Advanced Editor Text'

    spyOn($.fn, 'hide').andCallThrough()
    spyOn($.fn, 'show').andCallThrough()

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
          '#tab-1',  # tab_id
          'Tab 0'
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
      console.log 'data=', data
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

  describe "edit header properly hidden", ->
    it "hide header is True", ->
      waitsFor () ->
        if ($('.editor-with-tabs').data('hide-header') is 'True')
          # expect($.fn.hide).toHaveBeenCalled()
          if ($(".component-edit-header").css('display') is 'none')
            return true
        else
          if ($(".component-edit-header").css('display') isnt 'none')
            return true;
        return false;
      , "Timeout for header show/hide", 750
    

