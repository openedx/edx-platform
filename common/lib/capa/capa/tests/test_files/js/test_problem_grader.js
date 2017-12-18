/*
 * decaffeinate suggestions:
 * DS001: Remove Babel/TypeScript constructor workaround
 * DS102: Remove unnecessary code created because of implicit returns
 * DS207: Consider shorter variations of null checks
 * DS208: Avoid top-level this
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
class TestProblemGrader extends XProblemGrader {

  constructor(submission, problemState, parameters) {

    {
      // Hack: trick Babel/TypeScript into allowing this before super.
      if (false) { super(); }
      let thisFn = (() => { this; }).toString();
      let thisName = thisFn.slice(thisFn.indexOf('{') + 1, thisFn.indexOf(';')).trim();
      eval(`${thisName} = this;`);
    }
    this.submission = submission;
    this.problemState = problemState;
    if (parameters == null) { parameters = {}; }
    this.parameters = parameters;
    super(this.submission, this.problemState, this.parameters);
  }

  solve() {

    return this.solution = {0: this.problemState.value};
  }

  grade() {

    if ((this.solution == null)) {
      this.solve();
    }

    let allCorrect = true;

    for (let id in this.solution) {
      const value = this.solution[id];
      const valueCorrect = (this.submission != null) ? (value === this.submission[id]) : false;
      this.evaluation[id] = valueCorrect;
      if (!valueCorrect) {
        allCorrect = false;
      }
    }

    return allCorrect;
  }
}

const root = typeof exports !== 'undefined' && exports !== null ? exports : this;
root.graderClass = TestProblemGrader;
