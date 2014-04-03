describe "TabsEditingDescriptor", ->
  beforeEach ->
    @isInactiveClass = "is-inactive"
    @isCurrent = "current"
    loadFixtures 'tabs-edit.html'
    @descriptor = new TabsEditingDescriptor($('.xblock'))
    @html_id = 'test_id'
    @tab_0_switch = jasmine.createSpy('tab_0_switch');
    @tab_0_modelUpdate = jasmine.createSpy('tab_0_modelUpdate');
    @tab_1_switch = jasmine.createSpy('tab_1_switch');
    @tab_1_modelUpdate = jasmine.createSpy('tab_1_modelUpdate');
    TabsEditingDescriptor.Model.addModelUpdate(@html_id, 'Tab 0 Editor', @tab_0_modelUpdate)
    TabsEditingDescriptor.Model.addOnSwitch(@html_id, 'Tab 0 Editor', @tab_0_switch)
    TabsEditingDescriptor.Model.addModelUpdate(@html_id, 'Tab 1 Transcripts', @tab_1_modelUpdate)
    TabsEditingDescriptor.Model.addOnSwitch(@html_id, 'Tab 1 Transcripts', @tab_1_switch)

    spyOn($.fn, 'hide').andCallThrough()
    spyOn($.fn, 'show').andCallThrough()
    spyOn(TabsEditingDescriptor.Model, 'initialize')
    spyOn(TabsEditingDescriptor.Model, 'updateValue')

  afterEach ->
    TabsEditingDescriptor.Model.modules= {}

  describe "constructor", ->
    it "first tab should be visible", ->
      expect(@descriptor.$tabs.first()).toHaveClass(@isCurrent)
      expect(@descriptor.$content.first()).not.toHaveClass(@isInactiveClass)

  describe "onSwitchEditor", ->
    it "switching tabs changes styles", ->
      @descriptor.$tabs.eq(1).trigger("click")
      expect(@descriptor.$tabs.eq(0)).not.toHaveClass(@isCurrent)
      expect(@descriptor.$content.eq(0)).toHaveClass(@isInactiveClass)
      expect(@descriptor.$tabs.eq(1)).toHaveClass(@isCurrent)
      expect(@descriptor.$content.eq(1)).not.toHaveClass(@isInactiveClass)
      expect(@tab_1_switch).toHaveBeenCalled()

    it "if click on current tab, nothing should happen", ->
      spyOn($.fn, 'trigger').andCallThrough()
      currentTab = @descriptor.$tabs.filter('.' + @isCurrent)
      @descriptor.$tabs.eq(0).trigger("click")
      expect(@descriptor.$tabs.filter('.' + @isCurrent)).toEqual(currentTab)
      expect($.fn.trigger.calls.length).toEqual(1)

    it "onSwitch function call", ->
      @descriptor.$tabs.eq(1).trigger("click")
      expect(TabsEditingDescriptor.Model.updateValue).toHaveBeenCalled()
      expect(@tab_1_switch).toHaveBeenCalled()

  describe "save", ->
    it "function for current tab should be called", ->
      @descriptor.$tabs.eq(1).trigger("click")
      data = @descriptor.save().data
      expect(@tab_1_modelUpdate).toHaveBeenCalled()

    it "detach click event", ->
      spyOn($.fn, "off")
      @descriptor.save()
      expect($.fn.off).toHaveBeenCalledWith(
        'click',
        '.editor-tabs .tab',
        @descriptor.onSwitchEditor
      )

describe "TabsEditingDescriptor special save cases", ->
  beforeEach ->
    @isInactiveClass = "is-inactive"
    @isCurrent = "current"
    loadFixtures 'tabs-edit.html'
    @descriptor = new window.TabsEditingDescriptor($('.xblock'))
    @html_id = 'test_id'

  describe "save", ->
    it "case: no init", ->
      data = @descriptor.save().data
      expect(data).toEqual(null)

    it "case: no function in model update", ->
      TabsEditingDescriptor.Model.initialize(@html_id)
      data = @descriptor.save().data
      expect(data).toEqual(null)

    it "case: no function in model update, but value presented", ->
      @tab_0_modelUpdate = jasmine.createSpy('tab_0_modelUpdate').andReturn(1)
      TabsEditingDescriptor.Model.addModelUpdate(@html_id, 'Tab 0 Editor', @tab_0_modelUpdate)
      @descriptor.$tabs.eq(1).trigger("click")
      expect(@tab_0_modelUpdate).toHaveBeenCalled()
      data = @descriptor.save().data
      expect(data).toEqual(1)
