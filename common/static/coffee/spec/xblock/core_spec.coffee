describe "XBlock", ->
  beforeEach ->
    setFixtures """
      <div>
        <div class='xblock' id='vA' data-runtime-version="A" data-init="initFnA" data-name="a-name"/>
        <div>
          <div class='xblock' id='vZ' data-runtime-version="Z" data-init="initFnZ"/>
        </div>
        <div class='xblock' id='missing-version' data-init='initFnA' data-name='no-version'/>
        <div class='xblock' id='missing-init' data-runtime-version="A" data-name='no-init'/>
      </div>
      """

  describe "initializeBlock", ->
    beforeEach ->
      XBlock.runtime.vA = jasmine.createSpy().andReturn('runtimeA')
      XBlock.runtime.vZ = jasmine.createSpy().andReturn('runtimeZ')

      window.initFnA = jasmine.createSpy()
      window.initFnZ = jasmine.createSpy()

      @fakeChildren = ['list', 'of', 'children']
      spyOn(XBlock, 'initializeBlocks').andReturn(@fakeChildren)

      @vABlock = XBlock.initializeBlock($('#vA')[0])
      @vZBlock = XBlock.initializeBlock($('#vZ')[0])
      @missingVersionBlock = XBlock.initializeBlock($('#missing-version')[0])
      @missingInitBlock = XBlock.initializeBlock($('#missing-init')[0])

    it "loads the right runtime version", ->
      expect(XBlock.runtime.vA).toHaveBeenCalledWith($('#vA')[0], @fakeChildren)
      expect(XBlock.runtime.vZ).toHaveBeenCalledWith($('#vZ')[0], @fakeChildren)

    it "loads the right init function", ->
      expect(window.initFnA).toHaveBeenCalledWith('runtimeA', $('#vA')[0])
      expect(window.initFnZ).toHaveBeenCalledWith('runtimeZ', $('#vZ')[0])

    it "loads when missing versions", ->
      expect(@missingVersionBlock.element).toBe($('#missing-version'))
      expect(@missingVersionBlock.name).toBe('no-version')

    it "loads when missing init fn", ->
      expect(@missingInitBlock.element).toBe($('#missing-init'))
      expect(@missingInitBlock.name).toBe('no-init')

    it "adds names to blocks", ->
      expect(@vABlock.name).toBe('a-name')

    it "leaves leaves missing names undefined", ->
      expect(@vZBlock.name).toBeUndefined()

    it "attaches the element to the block", ->
      expect(@vABlock.element).toBe($('#vA')[0])
      expect(@vZBlock.element).toBe($('#vZ')[0])
      expect(@missingVersionBlock.element).toBe($('#missing-version')[0])
      expect(@missingInitBlock.element).toBe($('#missing-init')[0])

  describe "initializeBlocks", ->
    it "initializes children", ->
      spyOn(XBlock, 'initializeBlock')

      XBlock.initializeBlocks($('#jasmine-fixtures'))
      expect(XBlock.initializeBlock).toHaveBeenCalledWith($('#vA')[0])
      expect(XBlock.initializeBlock).toHaveBeenCalledWith($('#vZ')[0])
