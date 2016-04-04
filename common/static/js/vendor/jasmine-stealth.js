/* jasmine-stealth - 0.0.17
 * Makes Jasmine spies a bit more robust
 * https://github.com/searls/jasmine-stealth
 */
(function() {
  var __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  (function() {
    var Captor, fake, root, stubChainer, unfakes, whatToDoWhenTheSpyGetsCalled, _;
    root = (1, eval)('this');
    _ = function(obj) {
      return {
        each: function(iterator) {
          var item, _i, _len, _results;
          _results = [];
          for (_i = 0, _len = obj.length; _i < _len; _i++) {
            item = obj[_i];
            _results.push(iterator(item));
          }
          return _results;
        },
        isFunction: function() {
          return Object.prototype.toString.call(obj) === "[object Function]";
        },
        isString: function() {
          return Object.prototype.toString.call(obj) === "[object String]";
        }
      };
    };
    root.spyOnConstructor = function(owner, classToFake, methodsToSpy) {
      var fakeClass, spies;
      if (methodsToSpy == null) {
        methodsToSpy = [];
      }
      if (_(methodsToSpy).isString()) {
        methodsToSpy = [methodsToSpy];
      }
      spies = {
        constructor: jasmine.createSpy("" + classToFake + "'s constructor")
      };
      fakeClass = (function() {
        function _Class() {
          spies.constructor.apply(this, arguments);
        }

        return _Class;

      })();
      _(methodsToSpy).each(function(methodName) {
        spies[methodName] = jasmine.createSpy("" + classToFake + "#" + methodName);
        return fakeClass.prototype[methodName] = function() {
          return spies[methodName].apply(this, arguments);
        };
      });
      fake(owner, classToFake, fakeClass);
      return spies;
    };
    unfakes = [];
    afterEach(function() {
      _(unfakes).each(function(u) {
        return u();
      });
      return unfakes = [];
    });
    fake = function(owner, thingToFake, newThing) {
      var originalThing;
      originalThing = owner[thingToFake];
      owner[thingToFake] = newThing;
      return unfakes.push(function() {
        return owner[thingToFake] = originalThing;
      });
    };
    root.stubFor = root.spyOn;
    jasmine.createStub = jasmine.createSpy;
    jasmine.createStubObj = function(baseName, stubbings) {
      var name, obj, stubbing;
      if (stubbings.constructor === Array) {
        return jasmine.createSpyObj(baseName, stubbings);
      } else {
        obj = {};
        for (name in stubbings) {
          stubbing = stubbings[name];
          obj[name] = jasmine.createSpy(baseName + "." + name);
          if (_(stubbing).isFunction()) {
            obj[name].andCallFake(stubbing);
          } else {
            obj[name].andReturn(stubbing);
          }
        }
        return obj;
      }
    };
    whatToDoWhenTheSpyGetsCalled = function(spy) {
      var matchesStub, priorPlan;
      matchesStub = function(stubbing, args, context) {
        switch (stubbing.type) {
          case "args":
            return jasmine.getEnv().equals_(stubbing.ifThis, jasmine.util.argsToArray(args));
          case "context":
            return jasmine.getEnv().equals_(stubbing.ifThis, context);
        }
      };
      priorPlan = spy.plan;
      return spy.andCallFake(function() {
        var i, stubbing;
        i = 0;
        while (i < spy._stealth_stubbings.length) {
          stubbing = spy._stealth_stubbings[i];
          if (matchesStub(stubbing, arguments, this)) {
            if (stubbing.satisfaction === "callFake") {
              return stubbing.thenThat.apply(stubbing, arguments);
            } else {
              return stubbing.thenThat;
            }
          }
          i++;
        }
        return priorPlan.apply(spy, arguments);
      });
    };
    jasmine.Spy.prototype.whenContext = function(context) {
      var spy;
      spy = this;
      spy._stealth_stubbings || (spy._stealth_stubbings = []);
      whatToDoWhenTheSpyGetsCalled(spy);
      return stubChainer(spy, "context", context);
    };
    jasmine.Spy.prototype.when = function() {
      var ifThis, spy;
      spy = this;
      ifThis = jasmine.util.argsToArray(arguments);
      spy._stealth_stubbings || (spy._stealth_stubbings = []);
      whatToDoWhenTheSpyGetsCalled(spy);
      return stubChainer(spy, "args", ifThis);
    };
    stubChainer = function(spy, type, ifThis) {
      var addStubbing;
      addStubbing = function(satisfaction) {
        return function(thenThat) {
          spy._stealth_stubbings.unshift({
            type: type,
            ifThis: ifThis,
            satisfaction: satisfaction,
            thenThat: thenThat
          });
          return spy;
        };
      };
      return {
        thenReturn: addStubbing("return"),
        thenCallFake: addStubbing("callFake")
      };
    };
    jasmine.Spy.prototype.mostRecentCallThat = function(callThat, context) {
      var i;
      i = this.calls.length - 1;
      while (i >= 0) {
        if (callThat.call(context || this, this.calls[i]) === true) {
          return this.calls[i];
        }
        i--;
      }
    };
    jasmine.Matchers.ArgThat = (function(_super) {
      __extends(ArgThat, _super);

      function ArgThat(matcher) {
        this.matcher = matcher;
      }

      ArgThat.prototype.jasmineMatches = function(actual) {
        return this.matcher(actual);
      };

      return ArgThat;

    })(jasmine.Matchers.Any);
    jasmine.Matchers.ArgThat.prototype.matches = jasmine.Matchers.ArgThat.prototype.jasmineMatches;
    jasmine.argThat = function(expected) {
      return new jasmine.Matchers.ArgThat(expected);
    };
    jasmine.Matchers.Capture = (function(_super) {
      __extends(Capture, _super);

      function Capture(captor) {
        this.captor = captor;
      }

      Capture.prototype.jasmineMatches = function(actual) {
        this.captor.value = actual;
        return true;
      };

      return Capture;

    })(jasmine.Matchers.Any);
    jasmine.Matchers.Capture.prototype.matches = jasmine.Matchers.Capture.prototype.jasmineMatches;
    Captor = (function() {
      function Captor() {}

      Captor.prototype.capture = function() {
        return new jasmine.Matchers.Capture(this);
      };

      return Captor;

    })();
    return jasmine.captor = function() {
      return new Captor();
    };
  })();

}).call(this);