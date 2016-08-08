/* eslint-env node */

// Extensions to Jasmine.
//
// This file adds the following:
// 1. Custom matchers that may be helpful project-wise.
// 2. Copies of some matchers from Jasmine-jQuery.
//    Because Jasmine-Jquery uses its own version of JQuery, events registered in the code
//    using the platform version of JQuery are not "noticed" by Jasmine-jQuery matchers.
//    Similarly equality matching does not work either. So after the platform version of
//    jQuery has been loaded, we set these matchers up again in this module.

(function(root, factory) {
    if (typeof define === 'function' && define.amd) {
        require(['jquery'], function ($) {
            factory(root, $);
        });
    } else {
        factory(root, root.jQuery);
    }
}((function() {
    return this;
}()), function(window, $) {
    'use strict';

    // Add custom Jasmine matchers.
    beforeEach(function() {

        if (window.imagediff) {
            jasmine.addMatchers(window.imagediff.jasmine);
        }

        jasmine.addMatchers({
            toHaveAttrs: function() {
                return {
                    compare: function(actual, attrs) {
                        var result = {},
                            element = actual;

                        if ($.isEmptyObject(attrs)) {
                            return {
                                pass: false
                            };
                        }

                        result.pass = _.every(attrs, function(value, name) {
                            return element.attr(name) === value;
                        });

                        return result;
                    }
                };
            },
            toBeInRange: function() {
                return {
                    compare: function(actual, min, max) {
                        return {
                            pass: min <= actual && actual <= max
                        };
                    }
                };
            },
            toBeInArray: function() {
                return {
                    compare: function(actual, array) {
                        return {
                            pass: $.inArray(actual, array) > -1
                        };
                    }
                };
            },
            toBeInstanceOf: function() {
                // Assert the type of the value being tested matches the provided type
                return {
                    compare: function (actual, expected) {
                        return {
                            pass: actual instanceof expected
                        };
                    }
                };
            },
            toHaveIndex: function () {
                return {
                    compare: function (actual, expected) {
                        return {
                            pass: $(actual).index() === expected
                        };
                    }
                };
            },
            toXMLEqual: function() {
                return {
                    compare: function(actual, expected) {
                        return {
                            pass: actual.replace(/\s+/g, '') === expected.replace(/\s+/g, '')
                        };
                    }
                };
            }
        });
    });

    /* eslint-disable */
    // All the code below is taken from:
    // https://github.com/velesin/jasmine-jquery/blob/2.1.1/lib/jasmine-jquery.js
    beforeEach(function() {
        jasmine.addMatchers({
            toHandle: function() {
                return {
                    compare: function(actual, event) {
                        if (!actual || actual.length === 0) return {
                            pass: false
                        };
                        var events = $._data($(actual).get(0), "events");

                        if (!events || !event || typeof event !== "string") {
                            return {
                                pass: false
                            };
                        }

                        var namespaces = event.split("."),
                            eventType = namespaces.shift(),
                            sortedNamespaces = namespaces.slice(0).sort(),
                            namespaceRegExp = new RegExp("(^|\\.)" + sortedNamespaces.join("\\.(?:.*\\.)?") + "(\\.|$)");

                        if (events[eventType] && namespaces.length) {
                            for (var i = 0; i < events[eventType].length; i++) {
                                var namespace = events[eventType][i].namespace;

                                if (namespaceRegExp.test(namespace))
                                    return {
                                        pass: true
                                    };
                            }
                        } else {
                            return {
                                pass: (events[eventType] && events[eventType].length > 0)
                            };
                        }

                        return {
                            pass: false
                        };
                    }
                };
            },

            toHandleWith: function() {
                return {
                    compare: function(actual, eventName, eventHandler) {
                        if (!actual || actual.length === 0) return {
                            pass: false
                        };
                        var normalizedEventName = eventName.split('.')[0],
                            stack = $._data($(actual).get(0), "events")[normalizedEventName];

                        for (var i = 0; i < stack.length; i++) {
                            if (stack[i].handler == eventHandler) return {
                                pass: true
                            };
                        }

                        return {
                            pass: false
                        };
                    }
                };
            }
        });

        jasmine.addCustomEqualityTester(function(a, b) {
            if (a && b) {
                if (a instanceof $ || jasmine.isDomNode(a)) {
                    var $a = $(a);

                    if (b instanceof $)
                        return $a.length == b.length && a.is(b);

                    return $a.is(b);
                }

                if (b instanceof $ || jasmine.isDomNode(b)) {
                    var $b = $(b);

                    if (a instanceof $)
                        return a.length == $b.length && $b.is(a);

                    return $(b).is(a);
                }
            }
        });

        jasmine.addCustomEqualityTester(function(a, b) {
            if (a instanceof $ && b instanceof $ && a.size() == b.size())
                return a.is(b);
        });

    });

    var data = {
        spiedEvents: {},
        handlers: []
    };

    jasmine.jQuery.events = {
        spyOn: function(selector, eventName) {
            var handler = function(e) {
                var calls = (typeof data.spiedEvents[jasmine.spiedEventsKey(selector, eventName)] !== 'undefined') ? data.spiedEvents[jasmine.spiedEventsKey(selector, eventName)].calls : 0;
                data.spiedEvents[jasmine.spiedEventsKey(selector, eventName)] = {
                    args: jasmine.util.argsToArray(arguments),
                    calls: ++calls
                };
            };

            $(selector).on(eventName, handler);
            data.handlers.push(handler);

            return {
                selector: selector,
                eventName: eventName,
                handler: handler,
                reset: function() {
                    delete data.spiedEvents[jasmine.spiedEventsKey(selector, eventName)];
                },
                calls: {
                    count: function() {
                        return data.spiedEvents[jasmine.spiedEventsKey(selector, eventName)] ?
                            data.spiedEvents[jasmine.spiedEventsKey(selector, eventName)].calls : 0;
                    },
                    any: function() {
                        return data.spiedEvents[jasmine.spiedEventsKey(selector, eventName)] ?
                            !!data.spiedEvents[jasmine.spiedEventsKey(selector, eventName)].calls : false;
                    }
                }
            };
        },

        args: function(selector, eventName) {
            var actualArgs = data.spiedEvents[jasmine.spiedEventsKey(selector, eventName)].args;

            if (!actualArgs) {
                throw "There is no spy for " + eventName + " on " + selector.toString() + ". Make sure to create a spy using spyOnEvent.";
            }

            return actualArgs;
        },

        wasTriggered: function(selector, eventName) {
            return !!(data.spiedEvents[jasmine.spiedEventsKey(selector, eventName)]);
        },

        wasTriggeredWith: function(selector, eventName, expectedArgs, util, customEqualityTesters) {
            var actualArgs = jasmine.jQuery.events.args(selector, eventName).slice(1);

            if (Object.prototype.toString.call(expectedArgs) !== '[object Array]')
                actualArgs = actualArgs[0];

            return util.equals(actualArgs, expectedArgs, customEqualityTesters);
        },

        wasPrevented: function(selector, eventName) {
            var spiedEvent = data.spiedEvents[jasmine.spiedEventsKey(selector, eventName)],
                args = (jasmine.util.isUndefined(spiedEvent)) ? {} : spiedEvent.args,
                e = args ? args[0] : undefined;

            return e && e.isDefaultPrevented();
        },

        wasStopped: function(selector, eventName) {
            var spiedEvent = data.spiedEvents[jasmine.spiedEventsKey(selector, eventName)],
                args = (jasmine.util.isUndefined(spiedEvent)) ? {} : spiedEvent.args,
                e = args ? args[0] : undefined;

            return e && e.isPropagationStopped();
        },

        cleanUp: function() {
            data.spiedEvents = {};
            data.handlers = [];
        }
    };
    /* eslint-enable */
}));
