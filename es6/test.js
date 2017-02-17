((root, factory) => {
  'use strict';

  if (typeof define === 'function' && define.amd) {
    // Export as AMD, for RequireJS
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    // Export as CommonJS, for Node
    module.exports = factory();
  }
})(this, () => {
  'use strict';

  return () => {
    const propertyQuote = {
      bar: 'buzz',
      'mixed-quote-prop': 'mixed quotes are ok!',
    };
    const simpleESLintTest = 'This file should have no errors';

    if (propertyQuote.bar === 'X') {
      return false;
    }

    if (simpleESLintTest.charAt(0) === 'X') {
      return false;
    }

    return true;
  };
});
