/*
 * decaffeinate suggestions:
 * DS207: Consider shorter variations of null checks
 * DS208: Avoid top-level this
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
class XProblemGenerator {

  constructor(seed, parameters) {

    if (parameters == null) { parameters = {}; }
    this.parameters = parameters;
    this.random = new MersenneTwister(seed);

    this.problemState = {};
  }

  generate() {

    console.error("Abstract method called: XProblemGenerator.generate");
  }
}

class XProblemDisplay {

  constructor(state, submission, evaluation, container, submissionField, parameters) {
    this.state = state;
    this.submission = submission;
    this.evaluation = evaluation;
    this.container = container;
    this.submissionField = submissionField;
    if (parameters == null) { parameters = {}; }
    this.parameters = parameters;
  }

  render() {

    console.error("Abstract method called: XProblemDisplay.render");
  }

  updateSubmission() {

    this.submissionField.val(JSON.stringify(this.getCurrentSubmission()));
  }

  getCurrentSubmission() {
    console.error("Abstract method called: XProblemDisplay.getCurrentSubmission");
  }
}

class XProblemGrader {

  constructor(submission, problemState, parameters) {

    this.submission = submission;
    this.problemState = problemState;
    if (parameters == null) { parameters = {}; }
    this.parameters = parameters;
    this.solution   = null;
    this.evaluation = {};
  }

  solve() {

    console.error("Abstract method called: XProblemGrader.solve");
  }

  grade() {

    console.error("Abstract method called: XProblemGrader.grade");
  }
}

const root = typeof exports !== 'undefined' && exports !== null ? exports : this;

root.XProblemGenerator = XProblemGenerator;
root.XProblemDisplay   = XProblemDisplay;
root.XProblemGrader    = XProblemGrader;
