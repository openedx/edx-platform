describe "XBlock.Runtime.v1", ->
  beforeEach ->
    setFixtures """
      <div class='xblock' data-handler-prefix='/xblock/fake-usage-id/handler'/>
    """
    @children = [
      {name: 'childA'},
      {name: 'childB'}
    ]

    @element = $('.xblock')[0]
    $(@element).prop('xblock_children', @children)

    @runtime = new XBlock.Runtime.v1(@element)

  it "provides a list of children", ->
    expect(@runtime.children(@element)).toBe(@children)

  it "maps children by name", ->
    expect(@runtime.childMap(@element, 'childA')).toBe(@children[0])
    expect(@runtime.childMap(@element, 'childB')).toBe(@children[1])
