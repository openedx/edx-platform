define(function() {

  /**
   * Utility Functions
   */

  var toString = Object.prototype.toString;

  var isArray = function(arr) {
    return toString.call(arr) === '[object Array]';
  };

  var indexOf = function(arr, search) {
    for (var i = 0, length = arr.length; i < length; i++) {
      if (arr[i] === search) {
        return i;
      }
    }

    return -1;
  };

  var each = function(obj, iterator, context) {
    var breaker = {};

    if (obj === null) {
      return;
    }

    if (Array.prototype.forEach && obj.forEach === Array.prototype.forEach) {
      obj.forEach(iterator, context);
    } else if (obj.length === +obj.length) {
      for (var i = 0, l = obj.length; i < l; i++) {
        if (iterator.call(context, obj[i], i, obj) === breaker){
          return;
        }
      }
    } else {
      for (var key in obj) {
        if (obj.hasOwnProperty(key)) {
          if (iterator.call(context, obj[key], key, obj) === breaker) {
            return;
          }
        }
      }
    }
  };

  /**
   * Require.js Abstractions
   */

  var getContext = function(id) {
    return requirejs.s.contexts[id];
  };

  var undef = function(context, module) {
    if (context.undef) {
      return context.undef(module);
    }

    return context.require.undef(module);
  };

  /**
   * Create a context name incrementor.
   */
  var idCounter = 0;
  var uniqueId = function(prefix) {
    var id = idCounter++;
    return 'context' + id;
  };

  var Squire = function() {
    this.mocks = {};
    this._store = [];
    this.requiredCallbacks = [];
    this.configure.apply(this, arguments);
  };

  /**
   * Hook to call when the require function is called.
   */
  Squire.prototype.onRequired = function(cb) {
    this.requiredCallbacks.push(cb);
  };

  /**
   * Configuration of Squire.js, called from constructor or manually takes the
   * name of a require.js context to configure it.
   */
  Squire.prototype.configure = function(context) {
    var configuration = {};
    var property;

    this.id = uniqueId();

    // Default the context
    if (typeof context === 'undefined') {
      context = '_'; // Default require.js context
    }

    context = getContext(context);

    if ( ! context) {
      throw new Error('This context has not been created!');
    }

    each(context.config, function(property, key) {
      if (key !== 'deps') {
        configuration[key] = property;
      }
    });

    configuration.context = this.id;

    this.load = requirejs.config(configuration);
  };

  Squire.prototype.mock = function(path, mock) {
    var alias;
    if (typeof path === 'object') {
      each(path, function(alias, key) {
        this.mock(key, alias);
      }, this);
    } else {
      this.mocks[path] = mock;
    }

    return this;
  };

  Squire.prototype.store = function(path) {
    if (path && typeof path === 'string') {
      this._store.push(path);
    } else if(path && isArray(path)) {
      each(path, function(pathToStore) {
        this.store(pathToStore);
      }, this);
    }
    return this;
  };

  Squire.prototype.require = function(dependencies, callback, errback) {
    var magicModuleName = 'mocks';
    var self = this;
    var path, magicModuleLocation;

    magicModuleLocation = indexOf(dependencies, magicModuleName);

    if (magicModuleLocation !== -1) {
      dependencies.splice(magicModuleLocation, 1);
    }

    each(this.mocks, function(mock, path) {
      define(path, mock);
    });

    this.load(dependencies, function() {
      var store = {};
      var args = Array.prototype.slice.call(arguments);
      var dependency;

      if (magicModuleLocation !== -1) {
        each(self._store, function(dependency) {
          store[dependency] = getContext(self.id).defined[dependency];
        });

        args.splice(magicModuleLocation, 0, {
          mocks: self.mocks,
          store: store
        });
      }

      callback.apply(null, args);

      each(self.requiredCallbacks, function(cb) {
        cb.call(null, dependencies, args);
      });
    }, errback);
  };

  Squire.prototype.clean = function(mock) {
    var path;

    if (mock && typeof mock === 'string') {
      undef(getContext(this.id), mock);
      delete this.mocks[mock];
    } else if(mock && isArray(mock)) {
      each(mock, function(mockToClean) {
        this.clean(mockToClean);
      }, this);
    } else {
      each(this.mocks, function(mock, path){
        this.clean(path);
      }, this);
    }

    return this;
  };

  Squire.prototype.remove = function() {
    var path, context = getContext(this.id);
    if(!context) { return; }

    each(context.defined, function(dependency, path) {
      undef(context, path);
    }, this);

    delete requirejs.s.contexts[this.id];
  };

  Squire.prototype.run = function(deps, callback) {
    var self = this;
    var run = function(done) {
      self.require(deps, function() {
        callback.apply(null, arguments);
        done();
      });
    };

    run.toString = function() {
      return callback.toString();
    };

    return run;
  };

  /**
   * Utilities
   */

  Squire.Helpers = {};

  Squire.Helpers.returns = function(what) {
    return function() {
      return what;
    };
  };

  Squire.Helpers.constructs = function(what) {
    return function() {
      return function() {
        return what;
      };
    };
  };

  return Squire;
});
