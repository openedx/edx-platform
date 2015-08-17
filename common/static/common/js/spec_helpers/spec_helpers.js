/**
 * Generally useful helper functions for writing Jasmine unit tests.
 */
define([], function () {
    'use strict';

    /**
     * Runs func as a test case multiple times, using entries from data as arguments. Like Python's DDT.
     * @param data An object mapping test names to arrays of function parameters. The name is passed to it() as the name
     *      of the test case, and the list of arguments is applied as arguments to func.
     * @param func The function that actually expresses the logic of the test.
     */
    var withData = function (data, func) {
        for (var name in data) {
            if (data.hasOwnProperty(name)) {
                it(name, function () {
                    func.apply(this, data[name]);
                });
            }
        }
    };

    /**
     * Runs test multiple times, wrapping each call in a describe with beforeEach specified by setup and arguments and
     * name coming from entries in config.
     * @param config An object mapping configuration names to arrays of setup function parameters. The name is passed
     *      to describe as the name of the group of tests, and the list of arguments is applied as arguments to setup.
     * @param setup The function to setup the given configuration before each test case. Runs in beforeEach.
     * @param test The function that actually express the logic of the test. May include it() or more describe().
     */
    var withConfiguration = function (config, setup, test) {
        for (var name in config) {
            if (config.hasOwnProperty(name)) {
                describe(name, function () {
                    beforeEach(function () {
                        setup.apply(this, config[name]);
                    });
                    test();
                });
            }
        }
    };

    return {
        withData: withData,
        withConfiguration: withConfiguration
    };
});
