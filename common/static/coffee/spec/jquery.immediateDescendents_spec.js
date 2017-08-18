/*
 * decaffeinate suggestions:
 * DS102: Remove unnecessary code created because of implicit returns
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
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

    return this.descendents = $('#jasmine-fixtures').immediateDescendents(".xblock").get();
  });

  it("finds non-immediate children", function() {
    return expect(this.descendents).toContain($('#grandchild').get(0));
  });

  it("finds immediate children", function() {
    return expect(this.descendents).toContain($('#child').get(0));
  });

  it("skips nested descendents", function() {
    return expect(this.descendents).not.toContain($('#nested').get(0));
  });

  return it("finds 2 children", function() {
    return expect(this.descendents.length).toBe(2);
  });
});