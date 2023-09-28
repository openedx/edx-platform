/* eslint-env node */

// Custom library to replace the legacy non jasmine 2.0 compatible jasmine-stealth
(function(root, factory) {
    factory(root, root.jasmine, root._);
}((function() {
    return this;
}()), function(window, jasmine, _) {
    var fake, clearSpies, spyOnConstructor,
        unfakes = [];

    clearSpies = function() {
        _.each(unfakes, function(u) {
            return u();
        });
        // eslint-disable-next-line no-return-assign
        return unfakes = [];
    };

    fake = function(owner, thingToFake, newThing) {
        var originalThing;
        originalThing = owner[thingToFake];
        owner[thingToFake] = newThing;
        return unfakes.push(function() {
            // eslint-disable-next-line no-return-assign
            return owner[thingToFake] = originalThing;
        });
    };

    spyOnConstructor = function(owner, classToFake, methodsToSpy) {
        var fakeClass, spies;

        fakeClass = (function() {
            function _Class() {
                spies.constructor.apply(this, arguments);
            }

            return _Class;
        }());

        if (!methodsToSpy) {
            methodsToSpy = [];
        }

        if (_.isString(methodsToSpy)) {
            methodsToSpy = [methodsToSpy];
        }

        spies = {
            constructor: jasmine.createSpy('' + classToFake + '\'s constructor')
        };

        _.each(methodsToSpy, function(methodName) {
            spies[methodName] = jasmine.createSpy('' + classToFake + '#' + methodName);
            // eslint-disable-next-line no-return-assign
            return fakeClass.prototype[methodName] = function() {
                return spies[methodName].apply(this, arguments);
            };
        });

        fake(owner, classToFake, fakeClass);
        return spies;
    };

    jasmine.stealth = {
        spyOnConstructor: spyOnConstructor,
        clearSpies: clearSpies
    };
}));
