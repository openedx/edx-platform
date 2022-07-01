/**
 * Generally useful helper functions for writing Jasmine unit tests.
 *
 * @module SpecHelpers
 */
define([], function() {
    'use strict';

    var withData, withConfiguration;

    /**
     * Runs func as a test case multiple times, using entries from data as arguments.
     * You can think of this as like Python's DDT.
     *
     * @param {object} data An object mapping test names to arrays of function parameters.
     * The name is passed to it() as the name of the test case, and the list of arguments
     * is applied as arguments to func.
     * @param {function} func The function that actually expresses the logic of the test.
     */
    withData = function(data, func) {
        Object.keys(data).forEach(function(key) {
            it(key, function() {
                func.apply(this, data[key]);
            });
        });
    };

    /**
     * Runs test multiple times, wrapping each call in a describe with beforeEach
     * specified by setup and arguments and name coming from entries in config.
     *
     * @param {object} config An object mapping configuration names to arrays of setup
     * function parameters. The name is passed to describe as the name of the group
     * of tests, and the list of arguments is applied as arguments to setup.
     * @param {function} setup The function to setup the given configuration before
     * each test case. Runs in beforeEach.
     * @param {function} test The function that actually express the logic of the test.
     * May include it() or more describe().
     */
    withConfiguration = function(config, setup, test) {
        Object.keys(config).forEach(function(key) {
            describe(key, function() {
                beforeEach(function() {
                    setup.apply(this, config[key]);
                });
                test();
            });
        });
    };

    return {
        withData: withData,
        withConfiguration: withConfiguration
    };
});
