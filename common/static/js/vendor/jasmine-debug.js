/**
 * Jasmine debug for xmodule test suite.
 *
 * If you set `window.debugJasmineTests` to `true` then none of the it() calls
 * will run in the test suite files. This is intentional. To run 1 or more it()
 * calls, just add a prefix "_" - i.e. you should replace "it(" with "_it(".
 * This will accomplish running a single (or a few) it() tests for the purpose
 * of speeding up the process of debugging Jasmine tests.
 *
 * IMPORTANT: Do not forget to change `window.debugJasmineTests` back to
 * `false` before committing, along with any "_it(" to "it("!
 */

window.debugJasmineTests = false;

if (window.debugJasmineTests) {
    (function () {
        var oldIt = window.it;

        window.it = function () {};

        window._it = function() {
            return oldIt.apply(this, arguments);
        };
    }());
}

