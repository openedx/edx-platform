describe "$.immediateDescendents", ->
  beforeEach ->
    setFixtures """
      <div>
        <div class='xblock' id='child'>
          <div class='xblock' id='nested'/>
        </div>
        <div>
          <div class='xblock' id='grandchild'/>
        </div>
      </div>
      """

    @descendents = $('#jasmine-fixtures').immediateDescendents(".xblock").get()

  it "finds non-immediate children", ->
    expect(@descendents).toContain($('#grandchild').get(0))

  it "finds immediate children", ->
    expect(@descendents).toContain($('#child').get(0))

  it "skips nested descendents", ->
    expect(@descendents).not.toContain($('#nested').get(0))

  it "finds 2 children", ->
    expect(@descendents.length).toBe(2)