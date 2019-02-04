/*
 * decaffeinate suggestions:
 * DS001: Remove Babel/TypeScript constructor workaround
 * DS102: Remove unnecessary code created because of implicit returns
 * DS205: Consider reworking code to avoid use of IIFEs
 * DS207: Consider shorter variations of null checks
 * DS208: Avoid top-level this
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
class MinimaxProblemDisplay extends XProblemDisplay {

  constructor(state, submission, evaluation, container, submissionField, parameters) {

    {
      // Hack: trick Babel/TypeScript into allowing this before super.
      if (false) { super(); }
      let thisFn = (() => { this; }).toString();
      let thisName = thisFn.slice(thisFn.indexOf('{') + 1, thisFn.indexOf(';')).trim();
      eval(`${thisName} = this;`);
    }
    this.state = state;
    this.submission = submission;
    this.evaluation = evaluation;
    this.container = container;
    this.submissionField = submissionField;
    if (parameters == null) { parameters = {}; }
    this.parameters = parameters;
    super(this.state, this.submission, this.evaluation, this.container, this.submissionField, this.parameters);
  }

  render() {}

  createSubmission() {

    this.newSubmission = {};

    if (this.submission != null) {
      return (() => {
        const result = [];
        for (let id in this.submission) {
          const value = this.submission[id];
          result.push(this.newSubmission[id] = value);
        }
        return result;
      })();
    }
  }

  getCurrentSubmission() {
    return this.newSubmission;
  }
}

const root = typeof exports !== 'undefined' && exports !== null ? exports : this;
root.TestProblemDisplay = TestProblemDisplay;
