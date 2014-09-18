describe "XBlock", ->
  beforeEach ->
    setFixtures """
      <div>
        <div class='xblock'
             id='vA'
             data-runtime-version="A"
             data-runtime-class="TestRuntime"
             data-init="initFnA"
             data-name="a-name"
        />
        <div>
          <div class='xblock'
               id='vZ'
               data-runtime-version="Z"
               data-runtime-class="TestRuntime"
               data-init="initFnZ"
               data-request-token="req-token-z"
          />
        </div>
        <div class='xblock' id='missing-version' data-init='initFnA' data-name='no-version'/>
        <div class='xblock' id='missing-init' data-runtime-version="A" data-name='no-init'/>
      </div>
      """

  describe "initializeBlock", ->
    beforeEach ->
      window.TestRuntime = {}
      @runtimeA = {name: 'runtimeA'}
      @runtimeZ = {name: 'runtimeZ'}
      TestRuntime.vA = jasmine.createSpy().andReturn(@runtimeA)
      TestRuntime.vZ = jasmine.createSpy().andReturn(@runtimeZ)

      window.initFnA = jasmine.createSpy()
      window.initFnZ = jasmine.createSpy()

      @fakeChildren = ['list', 'of', 'children']
      spyOn(XBlock, 'initializeBlocks').andReturn(@fakeChildren)

      @vANode = $('#vA')[0]
      @vZNode = $('#vZ')[0]

      @vABlock = XBlock.initializeBlock(@vANode, 'req-token-a')
      @vZBlock = XBlock.initializeBlock(@vZNode)
      @missingVersionBlock = XBlock.initializeBlock($('#missing-version')[0])
      @missingInitBlock = XBlock.initializeBlock($('#missing-init')[0])

    it "loads the right runtime version", ->
      expect(TestRuntime.vA).toHaveBeenCalledWith()
      expect(TestRuntime.vZ).toHaveBeenCalledWith()

    it "loads the right init function", ->
      expect(window.initFnA).toHaveBeenCalledWith(@runtimeA, @vANode)
      expect(window.initFnZ).toHaveBeenCalledWith(@runtimeZ, @vZNode)

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
      expect(@vABlock.element).toBe(@vANode)
      expect(@vZBlock.element).toBe(@vZNode)
      expect(@missingVersionBlock.element).toBe($('#missing-version')[0])
      expect(@missingInitBlock.element).toBe($('#missing-init')[0])

    it "passes through the request token", ->
      expect(XBlock.initializeBlocks).toHaveBeenCalledWith($(@vANode), 'req-token-a')
      expect(XBlock.initializeBlocks).toHaveBeenCalledWith($(@vZNode), 'req-token-z')


  describe "initializeBlocks", ->
    beforeEach ->
      spyOn(XBlock, 'initializeBlock')

      @vANode = $('#vA')[0]
      @vZNode = $('#vZ')[0]

    it "initializes children", ->
      XBlock.initializeBlocks($('#jasmine-fixtures'))
      expect(XBlock.initializeBlock).toHaveBeenCalledWith(@vANode, undefined)
      expect(XBlock.initializeBlock).toHaveBeenCalledWith(@vZNode, undefined)

    it "only initializes matching request tokens", ->
      XBlock.initializeBlocks($('#jasmine-fixtures'), 'req-token-z')
      expect(XBlock.initializeBlock).not.toHaveBeenCalledWith(@vANode, jasmine.any(Object))
      expect(XBlock.initializeBlock).toHaveBeenCalledWith(@vZNode, 'req-token-z')
