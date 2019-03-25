describe("$.immediateDescendents", function() {
  beforeEach(function() {
    setFixtures(`\
<div>
  <div class='xblock' id='child'>
    <div class='xblock' id='nested'/>
  </div>
  <div>
    <div class='xblock' id='grandchild'/>
  </div>
</div>\
`
    );

    this.descendents = $('#jasmine-fixtures').immediateDescendents(".xblock").get();
  });

  it("finds non-immediate children", function() {
    expect(this.descendents).toContain($('#grandchild').get(0));
  });

  it("finds immediate children", function() {
    expect(this.descendents).toContain($('#child').get(0));
  });

  it("skips nested descendents", function() {
    expect(this.descendents).not.toContain($('#nested').get(0));
  });

  it("finds 2 children", function() {
    expect(this.descendents.length).toBe(2);
  });
});