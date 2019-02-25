/*
 * decaffeinate suggestions:
 * DS001: Remove Babel/TypeScript constructor workaround
 * DS207: Consider shorter variations of null checks
 * DS208: Avoid top-level this
 * Full docs: https://github.com/decaffeinate/decaffeinate/blob/master/docs/suggestions.md
 */
class TestProblemGenerator extends XProblemGenerator {

  constructor(seed, parameters) {

    {
      // Hack: trick Babel/TypeScript into allowing this before super.
      if (false) { super(); }
      let thisFn = (() => { this; }).toString();
      let thisName = thisFn.slice(thisFn.indexOf('{') + 1, thisFn.indexOf(';')).trim();
      eval(`${thisName} = this;`);
    }
    if (parameters == null) { parameters = {}; }
    this.parameters = parameters;
    super(seed, this.parameters);
  }

  generate() {

    this.problemState.value = this.parameters.value;

    return this.problemState;
  }
}

const root = typeof exports !== 'undefined' && exports !== null ? exports : this;
root.generatorClass = TestProblemGenerator;
