describe("TabsEditingDescriptor", function() {
  beforeEach(function() {
    this.isInactiveClass = "is-inactive";
    this.isCurrent = "current";
    loadFixtures('tabs-edit.html');
    this.descriptor = new TabsEditingDescriptor($('.xblock'));
    this.html_id = 'test_id';
    this.tab_0_switch = jasmine.createSpy('tab_0_switch');
    this.tab_0_modelUpdate = jasmine.createSpy('tab_0_modelUpdate');
    this.tab_1_switch = jasmine.createSpy('tab_1_switch');
    this.tab_1_modelUpdate = jasmine.createSpy('tab_1_modelUpdate');
    TabsEditingDescriptor.Model.addModelUpdate(this.html_id, 'Tab 0 Editor', this.tab_0_modelUpdate);
    TabsEditingDescriptor.Model.addOnSwitch(this.html_id, 'Tab 0 Editor', this.tab_0_switch);
    TabsEditingDescriptor.Model.addModelUpdate(this.html_id, 'Tab 1 Transcripts', this.tab_1_modelUpdate);
    TabsEditingDescriptor.Model.addOnSwitch(this.html_id, 'Tab 1 Transcripts', this.tab_1_switch);

    spyOn($.fn, 'hide').and.callThrough();
    spyOn($.fn, 'show').and.callThrough();
    spyOn(TabsEditingDescriptor.Model, 'initialize');
    spyOn(TabsEditingDescriptor.Model, 'updateValue');
  });

  afterEach(() => TabsEditingDescriptor.Model.modules= {});

  describe("constructor", () =>
    it("first tab should be visible", function() {
      expect(this.descriptor.$tabs.first()).toHaveClass(this.isCurrent);
      expect(this.descriptor.$content.first()).not.toHaveClass(this.isInactiveClass);
    })
  );

  describe("onSwitchEditor", function() {
    it("switching tabs changes styles", function() {
      this.descriptor.$tabs.eq(1).trigger("click");
      expect(this.descriptor.$tabs.eq(0)).not.toHaveClass(this.isCurrent);
      expect(this.descriptor.$content.eq(0)).toHaveClass(this.isInactiveClass);
      expect(this.descriptor.$tabs.eq(1)).toHaveClass(this.isCurrent);
      expect(this.descriptor.$content.eq(1)).not.toHaveClass(this.isInactiveClass);
      expect(this.tab_1_switch).toHaveBeenCalled();
    });

    it("if click on current tab, nothing should happen", function() {
      spyOn($.fn, 'trigger').and.callThrough();
      const currentTab = this.descriptor.$tabs.filter(`.${this.isCurrent}`);
      this.descriptor.$tabs.eq(0).trigger("click");
      expect(this.descriptor.$tabs.filter(`.${this.isCurrent}`)).toEqual(currentTab);
      expect($.fn.trigger.calls.count()).toEqual(1);
    });

    it("onSwitch function call", function() {
      this.descriptor.$tabs.eq(1).trigger("click");
      expect(TabsEditingDescriptor.Model.updateValue).toHaveBeenCalled();
      expect(this.tab_1_switch).toHaveBeenCalled();
    });
  });

  describe("save", function() {
    it("function for current tab should be called", function() {
      this.descriptor.$tabs.eq(1).trigger("click");
      const { data } = this.descriptor.save();
      expect(this.tab_1_modelUpdate).toHaveBeenCalled();
    });

    it("detach click event", function() {
      spyOn($.fn, "off");
      this.descriptor.save();
      expect($.fn.off).toHaveBeenCalledWith(
        'click',
        '.editor-tabs .tab',
        this.descriptor.onSwitchEditor
      );
    });
  });
});

describe("TabsEditingDescriptor special save cases", function() {
  beforeEach(function() {
    this.isInactiveClass = "is-inactive";
    this.isCurrent = "current";
    loadFixtures('tabs-edit.html');
    this.descriptor = new window.TabsEditingDescriptor($('.xblock'));
    this.html_id = 'test_id';
  });

  describe("save", function() {
    it("case: no init", function() {
      const { data } = this.descriptor.save();
      expect(data).toEqual(null);
    });

    it("case: no function in model update", function() {
      TabsEditingDescriptor.Model.initialize(this.html_id);
      const { data } = this.descriptor.save();
      expect(data).toEqual(null);
    });

    it("case: no function in model update, but value presented", function() {
      this.tab_0_modelUpdate = jasmine.createSpy('tab_0_modelUpdate').and.returnValue(1);
      TabsEditingDescriptor.Model.addModelUpdate(this.html_id, 'Tab 0 Editor', this.tab_0_modelUpdate);
      this.descriptor.$tabs.eq(1).trigger("click");
      expect(this.tab_0_modelUpdate).toHaveBeenCalled();
      const { data } = this.descriptor.save();
      expect(data).toEqual(1);
    });
  });
});
